from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

import concurrent.futures
import time

# Importing fastapi frameworks
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse

# importing functions from different files
from backend.database import warm_up_pool, fetch_one
from ussd_gateway.ussd_app import handle_ussd

app = FastAPI(title="FreshLink USSD API")

from backend.config import Config
from backend.database.connection import Base, engine
from backend.engine.scheduler import CoordinationScheduler
from backend import models
from backend.routes.accounts import dashboard_router, router as accounts_router
from backend.routes.admin import router as admin_router
from backend.routes.hub import router as hub_router
from backend.routes.payments import router as payments_router
from backend.routes.transporter import router as transporter_router


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(create_database=True, start_scheduler=True):
    @asynccontextmanager
    async def lifespan(app):
        if create_database:
            Base.metadata.create_all(bind=engine)
        scheduler = None
        if start_scheduler and Config.ENGINE_SCHEDULER_ENABLED:
            scheduler = CoordinationScheduler()
            scheduler.start()
        try:
            yield
        finally:
            if scheduler:
                scheduler.shutdown()

    api = FastAPI(title="FreshLink API", version="1.0.0", lifespan=lifespan)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.include_router(accounts_router)
    api.include_router(admin_router)
    api.include_router(hub_router)
    api.include_router(payments_router)
    api.include_router(transporter_router)
    api.include_router(dashboard_router)

    @api.get("/", include_in_schema=False)
    def landing_page():
        return RedirectResponse("/landing_page/index.html")

    api.mount(
        "/landing_page",
        StaticFiles(directory=FRONTEND_DIR / "landing_page"),
        name="landing_page",
    )
    api.mount("/shared", StaticFiles(directory=FRONTEND_DIR / "sevices"))
    api.mount("/admin/css", StaticFiles(directory=FRONTEND_DIR / "admin" / "css"))
    api.mount("/admin/js", StaticFiles(directory=FRONTEND_DIR / "admin" / "js"))
    api.mount(
        "/admin/images", StaticFiles(directory=FRONTEND_DIR / "admin" / "images")
    )
    api.mount(
        "/storagehub_dashboard/css",
        StaticFiles(directory=FRONTEND_DIR / "storagehub_dashboard" / "css"),
    )
    api.mount(
        "/storagehub_dashboard/js",
        StaticFiles(directory=FRONTEND_DIR / "storagehub_dashboard" / "js"),
    )
    api.mount(
        "/storagehub_dashboard/images",
        StaticFiles(directory=FRONTEND_DIR / "storagehub_dashboard" / "images"),
    )
    api.mount(
        "/transporter_dashboard/css",
        StaticFiles(directory=FRONTEND_DIR / "transporter_dashboard" / "css"),
    )
    api.mount(
        "/transporter_dashboard/js",
        StaticFiles(directory=FRONTEND_DIR / "transporter_dashboard" / "js"),
    )
    api.mount(
        "/transporter_dashboard/images",
        StaticFiles(directory=FRONTEND_DIR / "transporter_dashboard" / "images"),
    )

    @api.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    return api


app = create_app()

# Africa's talking ends a session if it goes beyond 10 seconds, so we 
# set out ussd timeout seconds to 10 as well
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
