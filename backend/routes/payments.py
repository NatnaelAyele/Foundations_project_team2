from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.config import Config
from backend.database.connection import get_db
from backend.models.provider import User
from backend.routes.accounts import get_current_user
from backend.services.payment_service import PaymentService, PaymentServiceError


router = APIRouter(prefix="/api/payments", tags=["Payments"])


class PaymentInitializeRequest(BaseModel):
    allocation_id: int = Field(gt=0)
    farmer_id: int | None = Field(default=None, gt=0)


class PaymentActionRequest(BaseModel):
    payment_id: int = Field(gt=0)


def service_error(error: PaymentServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=str(error))


def require_admin(user: User) -> None:
    if user.role.strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")


@router.post("/initialize")
def initialize_payment(
    payload: PaymentInitializeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
    try:
        return PaymentService(db).initialize_payment(
            payload.allocation_id,
            payload.farmer_id,
        )
    except PaymentServiceError as error:
        raise service_error(error) from error


@router.post("/verify")
def verify_payment(
    payload: PaymentActionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
    try:
        return PaymentService(db).verify_payment(payment_id=payload.payment_id)
    except PaymentServiceError as error:
        raise service_error(error) from error


@router.post("/refund")
def refund_payment(
    payload: PaymentActionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
    try:
        return PaymentService(db).refund_payment(payload.payment_id)
    except PaymentServiceError as error:
        raise service_error(error) from error


@router.post("/flutterwave/webhook")
async def flutterwave_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("flutterwave-signature")
    try:
        payload = await request.json()
        return PaymentService(db).process_webhook(raw_body, signature, payload)
    except PaymentServiceError as error:
        raise service_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from error


@router.get("/flutterwave/callback")
def flutterwave_callback(
    tx_ref: str | None = None,
    transaction_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        payment = PaymentService(db).process_callback(tx_ref, transaction_id, status)
        result = "success" if payment["status"] == "PAID" else "failed"
    except PaymentServiceError:
        result = "failed"
    return RedirectResponse(
        f"{Config.FRONTEND_BASE_URL}/landing_page/index.html?payment_status={result}"
    )


@router.get("/allocation/{allocation_id}")
def get_payments_by_allocation(
    allocation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return {
            "items": PaymentService(db).get_payments_by_allocation(
                allocation_id,
                user,
            )
        }
    except PaymentServiceError as error:
        raise service_error(error) from error


@router.get("/farmer/{farmer_id}")
def get_payments_by_farmer(
    farmer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return {"items": PaymentService(db).get_payments_by_farmer(farmer_id, user)}
    except PaymentServiceError as error:
        raise service_error(error) from error


@router.get("/{payment_id}")
def get_payment(
    payment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PaymentService(db).get_payment(payment_id, user)
    except PaymentServiceError as error:
        raise service_error(error) from error
