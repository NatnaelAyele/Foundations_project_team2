# backend/main.py

import concurrent.futures
import time

from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse

from backend.database import warm_up_pool, fetch_one
from ussd_gateway.ussd_app import handle_ussd

app = FastAPI(title="FreshLink USSD API")

# Africa's Talking drops the session if we take too long, so we cap
# how long we are willing to wait for our own logic.
USSD_TIMEOUT_SECONDS = 10

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


@app.on_event("startup")
def on_startup():
    """
    Opens the database pool before the first USSD request arrives,
    so no farmer pays the connection cost inside their session.
    """
    warm_up_pool()


@app.get("/")
def home():
    return {"message": "FreshLink FastAPI backend is running"}


@app.get("/health/db")
def health_db():
    """
    Quick check that the database is reachable and how slow it is.
    Open this in a browser before demoing.
    """
    start = time.time()
    try:
        fetch_one("SELECT 1 AS ok")
        return {"database": "ok", "seconds": round(time.time() - start, 3)}
    except Exception as error:
        return {"database": "error", "detail": str(error)}


@app.post("/api/ussd", response_class=PlainTextResponse)
def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form("")
):
    """
    Receives USSD requests from Africa's Talking.

    The endpoint must never crash and must never hang, because both
    cause the "network is experiencing technical problems" message.
    """
    try:
        print("\n========== USSD REQUEST ==========")
        print(f"sessionId: {sessionId}")
        print(f"serviceCode: {serviceCode}")
        print(f"phoneNumber: {phoneNumber}")
        print(f"text: {text}")
        print("==================================\n")

        latest_reply = text.split("*")[-1] if text else ""

        started = time.time()

        future = _executor.submit(
            handle_ussd,
            phone_number=phoneNumber,
            message=latest_reply,
            session_id=sessionId
        )

        try:
            response = future.result(timeout=USSD_TIMEOUT_SECONDS)
        except concurrent.futures.TimeoutError:
            print("\n========== USSD TIMEOUT ==========")
            print("handle_ussd exceeded the time limit.")
            print("Open /health/db - the database is probably slow.")
            print("==================================\n")
            return "END FreshLink is taking too long to respond. Please dial again."

        elapsed = time.time() - started

        if not response.startswith("CON ") and not response.startswith("END "):
            return "END Sorry, FreshLink returned an invalid response."

        print("\n========== USSD RESPONSE ==========")
        print(f"(handled in {elapsed:.2f}s)")
        print(response)
        print("===================================\n")

        return response

    except Exception as error:
        print("\n========== USSD ERROR ==========")
        print(error)
        print("===============================\n")

        return "END Sorry, FreshLink is currently unavailable. Please try again later."