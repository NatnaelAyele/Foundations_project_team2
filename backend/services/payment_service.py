import hashlib
import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.Flutterwave.gateways.flutterwave import (
    FlutterwaveGateway,
    FlutterwaveGatewayError,
)
from backend.Flutterwave.payment import PaymentError, PaymentManager
from backend.models.operations import (
    ForecastAllocation,
    HarvestForecast,
    Notification,
    Payment,
    PaymentWebhookEvent,
    TripAllocation,
)
from backend.models.provider import ColdHub, ColdHubAccount, Farmer, Transporter, Truck, User


logger = logging.getLogger(__name__)


class PaymentServiceError(RuntimeError):
    status_code = 400


class AllocationNotFoundError(PaymentServiceError):
    status_code = 404


class FarmerNotFoundError(PaymentServiceError):
    status_code = 404


class PaymentNotFoundError(PaymentServiceError):
    status_code = 404


class PaymentPermissionError(PaymentServiceError):
    status_code = 403


class PaymentConflictError(PaymentServiceError):
    status_code = 409


class PaymentGatewayUnavailableError(PaymentServiceError):
    status_code = 502


class InvalidWebhookSignatureError(PaymentServiceError):
    status_code = 401


class PaymentStatus:
    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


VALID_TRANSITIONS = {
    PaymentStatus.CREATED: {
        PaymentStatus.INITIALIZED,
        PaymentStatus.PENDING,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.INITIALIZED: {
        PaymentStatus.PENDING,
        PaymentStatus.PAID,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.PENDING: {
        PaymentStatus.PAID,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.PAID: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: set(),
    PaymentStatus.CANCELLED: set(),
    PaymentStatus.REFUNDED: set(),
}


class PaymentService:
    """Coordinates payment persistence, provider calls, and notifications."""

    def __init__(
        self,
        db: Session,
        gateway=None,
        payment_manager: PaymentManager | None = None,
    ):
        self.db = db
        self.gateway = gateway or FlutterwaveGateway()
        self.payment_manager = payment_manager or PaymentManager(gateway=self.gateway)

    def initialize_payment(
        self,
        allocation_id: int,
        farmer_id: int | None = None,
        auto_commit: bool = True,
    ) -> dict:
        try:
            allocation = self.get_allocation_or_raise(allocation_id)
            farmer = self.get_farmer_for_payment(allocation_id, farmer_id)
            existing = self.get_existing_payment(allocation_id, farmer.farmer_id)
            payment = None
            if existing:
                if existing.status == PaymentStatus.PAID:
                    raise PaymentConflictError("Payment is already completed")
                if (
                    existing.status in {PaymentStatus.INITIALIZED, PaymentStatus.PENDING}
                    and existing.payment_link
                ):
                    return self.payment_to_dict(existing)
                if existing.status == PaymentStatus.CREATED and not existing.payment_link:
                    payment = existing

            if payment is None:
                payment = self.create_payment_record(
                    allocation_id,
                    farmer.farmer_id,
                    auto_commit=False,
                    allocation=allocation,
                    farmer=farmer,
                )
            self.db.flush()

            self.initialize_existing_payment_record(payment)
            self.db.flush()

            if auto_commit:
                self.db.commit()
                self.db.refresh(payment)

            return self.payment_to_dict(payment)
        except (PaymentServiceError, PaymentError, SQLAlchemyError, FlutterwaveGatewayError) as error:
            if auto_commit:
                self.db.rollback()
            if isinstance(error, PaymentServiceError):
                raise
            if isinstance(error, FlutterwaveGatewayError):
                raise PaymentGatewayUnavailableError(str(error)) from error
            raise PaymentServiceError(str(error)) from error

    def create_payment(
        self,
        allocation_id: int,
        farmer_id: int | None = None,
        auto_commit: bool = True,
    ) -> dict:
        return self.initialize_payment(allocation_id, farmer_id, auto_commit)

    def create_payment_record(
        self,
        allocation_id: int,
        farmer_id: int | None = None,
        auto_commit: bool = True,
        allocation: TripAllocation | None = None,
        farmer: Farmer | None = None,
    ) -> Payment:
        allocation = allocation or self.get_allocation_or_raise(allocation_id)
        farmer = farmer or self.get_farmer_for_payment(allocation_id, farmer_id)
        existing = self.get_existing_payment(allocation_id, farmer.farmer_id)
        if existing and existing.status in {
            PaymentStatus.CREATED,
            PaymentStatus.INITIALIZED,
            PaymentStatus.PENDING,
            PaymentStatus.PAID,
        }:
            return existing

        reservation = self.build_reservation(allocation, farmer)
        payment_data = self.payment_manager.create_payment(reservation)
        payment = self.persist_payment(payment_data, allocation, farmer)
        if auto_commit:
            self.db.commit()
            self.db.refresh(payment)
        return payment

    def initialize_existing_payment_record(
        self,
        payment: Payment,
        auto_commit: bool = False,
    ) -> dict:
        if payment.status == PaymentStatus.PAID:
            raise PaymentConflictError("Payment is already completed")
        if payment.status in {PaymentStatus.INITIALIZED, PaymentStatus.PENDING} and payment.payment_link:
            return self.payment_to_dict(payment)
        if payment.status not in {PaymentStatus.CREATED, PaymentStatus.INITIALIZED, PaymentStatus.PENDING}:
            raise PaymentConflictError("Create a new payment before reinitializing this status")

        gateway_response = self.gateway.initialize_payment(self.payment_to_manager_dict(payment))
        payment.payment_link = gateway_response["payment_link"]
        payment.tx_ref = gateway_response.get("tx_ref") or payment.tx_ref
        payment.flutterwave_ref = payment.tx_ref
        payment.provider_status = gateway_response.get("provider_status")
        payment.provider_response = gateway_response.get("raw_response")
        if payment.status == PaymentStatus.CREATED:
            self.apply_status(payment, PaymentStatus.INITIALIZED)
        else:
            self.create_payment_notification(payment, "PAYMENT_INITIALIZED")
        self.db.flush()
        if auto_commit:
            self.db.commit()
            self.db.refresh(payment)
        return self.payment_to_dict(payment)

    def verify_payment(
        self,
        payment_id: int | None = None,
        tx_ref: str | None = None,
        transaction_id: str | None = None,
        auto_commit: bool = True,
    ) -> dict:
        payment = self.get_payment_for_verification(payment_id, tx_ref)
        if payment.status in {PaymentStatus.PAID, PaymentStatus.REFUNDED}:
            return self.payment_to_dict(payment)

        try:
            response = self.gateway.verify_payment(
                payment.tx_ref,
                transaction_id=transaction_id or payment.transaction_id,
            )
            self.apply_verified_response(payment, response)
            if auto_commit:
                self.db.commit()
                self.db.refresh(payment)
            return self.payment_to_dict(payment)
        except (PaymentServiceError, SQLAlchemyError, FlutterwaveGatewayError) as error:
            if auto_commit:
                self.db.rollback()
            if isinstance(error, PaymentServiceError):
                raise
            if isinstance(error, FlutterwaveGatewayError):
                raise PaymentGatewayUnavailableError(str(error)) from error
            raise PaymentServiceError(str(error)) from error

    def refund_payment(self, payment_id: int, auto_commit: bool = True) -> dict:
        payment = self.get_payment_or_raise(payment_id)
        if payment.status == PaymentStatus.REFUNDED:
            return self.payment_to_dict(payment)
        if payment.status != PaymentStatus.PAID:
            raise PaymentConflictError("Only paid payments can be refunded")

        try:
            response = self.gateway.refund_payment(
                payment.tx_ref,
                transaction_id=payment.transaction_id,
                amount=payment.amount,
                reason="FreshLink refund",
            )
            payment.provider_status = response.get("provider_status")
            payment.provider_response = response.get("raw_response")
            self.apply_status(payment, PaymentStatus.REFUNDED)
            if auto_commit:
                self.db.commit()
                self.db.refresh(payment)
            return self.payment_to_dict(payment)
        except (PaymentServiceError, SQLAlchemyError, FlutterwaveGatewayError) as error:
            if auto_commit:
                self.db.rollback()
            if isinstance(error, PaymentServiceError):
                raise
            if isinstance(error, FlutterwaveGatewayError):
                raise PaymentGatewayUnavailableError(str(error)) from error
            raise PaymentServiceError(str(error)) from error

    def process_webhook(self, raw_body: bytes, signature: str | None, payload: dict) -> dict:
        try:
            if not self.gateway.verify_webhook_signature(raw_body, signature):
                raise InvalidWebhookSignatureError("Invalid Flutterwave webhook signature")

            data = payload.get("data") or {}
            tx_ref = data.get("tx_ref") or data.get("txRef") or payload.get("tx_ref") or payload.get("txRef")
            transaction_id = data.get("id") or data.get("transaction_id") or payload.get("id") or payload.get("transaction_id")
            event_type = (
                payload.get("type")
                or payload.get("event")
                or payload.get("event_type")
                or data.get("type")
                or data.get("event")
                or data.get("event_type")
            )
            provider_status = data.get("status") or payload.get("status")
            event_id = self.build_webhook_event_id(
                payload,
                data,
                raw_body,
                tx_ref=tx_ref,
                transaction_id=transaction_id,
                event_type=event_type,
                provider_status=provider_status,
            )

            existing = self.db.get(PaymentWebhookEvent, str(event_id))
            if existing is not None:
                return {"ok": True, "duplicate": True, "event_id": str(event_id)}

            payment = self.get_payment_for_verification(None, tx_ref)
            verification_response = self.gateway.verify_payment(
                payment.tx_ref,
                transaction_id=str(transaction_id) if transaction_id is not None else None,
            )
            self.db.rollback()

            existing = self.db.get(PaymentWebhookEvent, str(event_id))
            if existing is not None:
                return {"ok": True, "duplicate": True, "event_id": str(event_id)}

            payment = self.get_payment_for_verification(None, tx_ref)
            event = PaymentWebhookEvent(
                event_id=str(event_id),
                payment_id=payment.payment_id,
                tx_ref=tx_ref,
                event_type=event_type,
                provider_status=provider_status,
                payload=payload,
            )
            self.db.add(event)
            self.db.flush()
            self.apply_verified_response(payment, verification_response)
            self.db.commit()
            return {"ok": True, "duplicate": False, "event_id": str(event_id)}
        except IntegrityError as error:
            self.db.rollback()
            if self.is_duplicate_webhook_event_error(error, event_id if "event_id" in locals() else None):
                return {"ok": True, "duplicate": True, "event_id": str(event_id)}
            logger.exception("Unexpected database integrity error while processing payment webhook")
            raise
        except Exception:
            self.db.rollback()
            raise

    def process_callback(
        self,
        tx_ref: str | None,
        transaction_id: str | None,
        provider_status: str | None,
    ) -> dict:
        try:
            if not tx_ref:
                raise PaymentServiceError("Invalid callback: tx_ref is required")
            payment = self.get_payment_for_verification(None, tx_ref)
            return self.verify_payment(
                payment_id=payment.payment_id,
                transaction_id=transaction_id,
            )
        except Exception:
            self.db.rollback()
            raise

    def ensure_trip_can_start(self, allocation_id: int) -> None:
        payments = self.db.scalars(
            select(Payment).where(Payment.allocation_id == allocation_id)
        ).all()
        if not payments or not any(payment.status == PaymentStatus.PAID for payment in payments):
            raise PaymentPermissionError(
                "Payment must be completed before this trip can be started"
            )

    def get_payment(self, payment_id: int, user: User | None = None) -> dict:
        payment = self.get_payment_or_raise(payment_id)
        self.ensure_user_can_view_payment(user, payment)
        return self.payment_to_dict(payment)

    def get_payments_by_farmer(self, farmer_id: int, user: User | None = None) -> list[dict]:
        if self.db.get(Farmer, farmer_id) is None:
            raise FarmerNotFoundError("Farmer not found")
        payments = self.db.scalars(
            select(Payment)
            .where(Payment.farmer_id == farmer_id)
            .order_by(Payment.created_at.desc(), Payment.payment_id.desc())
        ).all()
        for payment in payments:
            self.ensure_user_can_view_payment(user, payment)
        return [self.payment_to_dict(payment) for payment in payments]

    def get_payments_by_allocation(
        self,
        allocation_id: int,
        user: User | None = None,
    ) -> list[dict]:
        self.get_allocation_or_raise(allocation_id)
        payments = self.db.scalars(
            select(Payment)
            .where(Payment.allocation_id == allocation_id)
            .order_by(Payment.created_at.desc(), Payment.payment_id.desc())
        ).all()
        for payment in payments:
            self.ensure_user_can_view_payment(user, payment)
        return [self.payment_to_dict(payment) for payment in payments]

    def payment_summary(self) -> dict:
        rows = self.db.execute(
            select(Payment.status, func.count(Payment.payment_id), func.coalesce(func.sum(Payment.amount), 0))
            .group_by(Payment.status)
        ).all()
        counts = {status.lower(): count for status, count, _ in rows}
        sums = {status.lower(): float(total) for status, _, total in rows}
        return {
            "total": sum(counts.values()),
            "paid": counts.get("paid", 0),
            "pending": counts.get("pending", 0) + counts.get("initialized", 0) + counts.get("created", 0),
            "failed": counts.get("failed", 0) + counts.get("cancelled", 0),
            "refunded": counts.get("refunded", 0),
            "revenue": sums.get("paid", 0.0),
            "outstanding_balances": (
                sums.get("pending", 0.0)
                + sums.get("initialized", 0.0)
                + sums.get("created", 0.0)
            ),
        }

    def update_payment_status(
        self,
        payment_id: int,
        status: str,
        auto_commit: bool = True,
    ) -> dict:
        payment = self.get_payment_or_raise(payment_id)
        self.apply_status(payment, status)
        if auto_commit:
            self.db.commit()
            self.db.refresh(payment)
        return self.payment_to_dict(payment)

    def apply_verified_response(self, payment: Payment, response: dict) -> None:
        expected_amount = Decimal(str(payment.amount))
        response_amount = Decimal(str(response.get("amount") or "0"))
        provider_status = response.get("provider_status")
        next_status = response.get("payment_status") or PaymentStatus.PENDING
        if next_status == PaymentStatus.PAID:
            if response.get("tx_ref") != payment.tx_ref:
                raise PaymentConflictError("Flutterwave transaction reference mismatch")
            if response.get("currency") != payment.currency:
                raise PaymentConflictError("Flutterwave transaction currency mismatch")
            if response_amount < expected_amount:
                raise PaymentConflictError("Flutterwave transaction amount is too low")
        transaction_id = response.get("transaction_id")
        if transaction_id is not None and str(transaction_id).strip():
            payment.transaction_id = str(transaction_id)
        payment.flutterwave_ref = response.get("flutterwave_ref") or payment.flutterwave_ref
        payment.provider_status = provider_status
        payment.provider_response = response.get("raw_response")
        payment.verified_at = datetime.now()
        payment.last_checked_at = datetime.now()
        self.apply_status(payment, next_status)

    def apply_status(self, payment: Payment, next_status: str) -> None:
        if next_status not in VALID_TRANSITIONS:
            raise PaymentServiceError("Unsupported payment status")
        if payment.status == next_status:
            return
        if next_status not in VALID_TRANSITIONS.get(payment.status, set()):
            raise PaymentConflictError(
                f"Cannot change payment status from {payment.status} to {next_status}"
            )
        payment.status = next_status
        now = datetime.now()
        if next_status == PaymentStatus.INITIALIZED:
            self.create_payment_notification(payment, "PAYMENT_INITIALIZED")
        elif next_status == PaymentStatus.PENDING:
            self.create_payment_notification(payment, "PAYMENT_PENDING")
        elif next_status == PaymentStatus.PAID:
            payment.paid_at = now
            payment.settled_at = now
            self.create_payment_notification(payment, "PAYMENT_SUCCESSFUL")
        elif next_status == PaymentStatus.FAILED:
            payment.failed_at = now
            self.create_payment_notification(payment, "PAYMENT_FAILED")
        elif next_status == PaymentStatus.REFUNDED:
            payment.refunded_at = now
            self.create_payment_notification(payment, "PAYMENT_REFUNDED")

    def get_allocation_or_raise(self, allocation_id: int) -> TripAllocation:
        allocation = self.db.get(TripAllocation, allocation_id)
        if allocation is None:
            raise AllocationNotFoundError("Allocation not found")
        return allocation

    def get_payment_or_raise(self, payment_id: int) -> Payment:
        payment = self.db.get(Payment, payment_id)
        if payment is None:
            raise PaymentNotFoundError("Payment not found")
        return payment

    def get_payment_for_verification(
        self,
        payment_id: int | None,
        tx_ref: str | None,
    ) -> Payment:
        if payment_id is not None:
            return self.get_payment_or_raise(payment_id)
        if not tx_ref:
            raise PaymentNotFoundError("Payment reference is required")
        payment = self.db.scalar(select(Payment).where(Payment.tx_ref == tx_ref).limit(1))
        if payment is None:
            raise PaymentNotFoundError("Payment not found")
        return payment

    def get_farmer_for_payment(
        self,
        allocation_id: int,
        farmer_id: int | None,
    ) -> Farmer:
        if farmer_id is not None:
            farmer = self.db.get(Farmer, farmer_id)
            if farmer is None:
                raise FarmerNotFoundError("Farmer not found")
            linked = self.db.scalar(
                select(ForecastAllocation)
                .join(HarvestForecast, HarvestForecast.forecast_id == ForecastAllocation.forecast_id)
                .where(
                    ForecastAllocation.allocation_id == allocation_id,
                    HarvestForecast.farmer_id == farmer_id,
                )
            )
            if linked is None:
                raise FarmerNotFoundError("Farmer is not linked to this allocation")
            return farmer

        farmer = self.db.scalar(
            select(Farmer)
            .join(HarvestForecast, HarvestForecast.farmer_id == Farmer.farmer_id)
            .join(ForecastAllocation, ForecastAllocation.forecast_id == HarvestForecast.forecast_id)
            .where(ForecastAllocation.allocation_id == allocation_id)
            .order_by(Farmer.farmer_id)
            .limit(1)
        )
        if farmer is None:
            raise FarmerNotFoundError("No farmer is linked to this allocation")
        return farmer

    def get_existing_payment(self, allocation_id: int, farmer_id: int) -> Payment | None:
        return self.db.scalar(
            select(Payment)
            .where(Payment.allocation_id == allocation_id, Payment.farmer_id == farmer_id)
            .order_by(Payment.payment_id.desc())
            .limit(1)
        )

    def build_reservation(self, allocation: TripAllocation, farmer: Farmer) -> dict:
        truck = self.db.get(Truck, allocation.truck_id)
        hub = self.db.get(ColdHub, allocation.hub_id)
        transporter = self.db.get(Transporter, truck.transporter_id) if truck else None
        forecasts = self.get_allocation_forecasts(allocation.allocation_id)
        return {
            "allocation_id": allocation.allocation_id,
            "truck_id": allocation.truck_id,
            "hub_id": allocation.hub_id,
            "sector_id": allocation.sector_id,
            "status": "RESERVED",
            "total_load_kg": allocation.total_load_kg,
            "farmer_id": farmer.farmer_id,
            "farmer_phone": farmer.phone,
            "farmer_phones": [farmer.phone],
            "transporter_phone": transporter.phone if transporter else None,
            "hub_phone": hub.phone if hub else None,
            "forecasts": forecasts,
        }

    def get_allocation_forecasts(self, allocation_id: int) -> list[dict]:
        rows = self.db.execute(
            select(ForecastAllocation, HarvestForecast, Farmer)
            .join(HarvestForecast, HarvestForecast.forecast_id == ForecastAllocation.forecast_id)
            .join(Farmer, Farmer.farmer_id == HarvestForecast.farmer_id)
            .where(ForecastAllocation.allocation_id == allocation_id)
        ).all()
        return [
            {
                "forecast_id": forecast.forecast_id,
                "farmer_id": farmer.farmer_id,
                "farmer_phone": farmer.phone,
                "quantity_kg": allocation.allocated_quantity_kg,
            }
            for allocation, forecast, farmer in rows
        ]

    def persist_payment(self, payment_data: dict, allocation: TripAllocation, farmer: Farmer) -> Payment:
        amount = Decimal(str(payment_data["amount"]))
        if amount <= 0:
            raise PaymentServiceError("Payment amount must be greater than zero")
        payment = Payment(
            allocation_id=allocation.allocation_id,
            farmer_id=farmer.farmer_id,
            payer_type=payment_data["payer_type"],
            payee_type=payment_data["payee_type"],
            payer_phone=payment_data.get("payer_phone"),
            payee_phone=payment_data.get("payee_phone"),
            amount=amount,
            currency=payment_data["currency"],
            purpose=payment_data["purpose"],
            payment_method=payment_data["payment_method"],
            status=PaymentStatus.CREATED,
            payment_reference=payment_data["payment_reference"],
            flutterwave_ref=payment_data.get("flutterwave_ref"),
            tx_ref=payment_data.get("tx_ref"),
        )
        self.db.add(payment)
        return payment

    def create_payment_notification(self, payment: Payment, event: str) -> None:
        farmer = self.db.get(Farmer, payment.farmer_id)
        if farmer is None:
            return
        messages = {
            "PAYMENT_INITIALIZED": (
                f"FreshLink payment initialized. Amount: {payment.amount} {payment.currency}. "
                f"Pay here: {payment.payment_link}"
            ),
            "PAYMENT_PENDING": "FreshLink payment is pending confirmation.",
            "PAYMENT_SUCCESSFUL": "Your FreshLink payment has been confirmed successfully.",
            "PAYMENT_FAILED": "Your FreshLink payment failed. Please retry or contact support.",
            "PAYMENT_REFUNDED": "Your FreshLink refund has been initiated.",
        }
        self.db.add(
            Notification(
                recipient_type="FARMER",
                recipient_phone=farmer.phone,
                channel="SMS",
                message=messages[event],
                status="QUEUED",
                related_trip_id=payment.allocation_id,
            )
        )

    def build_webhook_event_id(
        self,
        payload: dict,
        data: dict,
        raw_body: bytes | None = None,
        tx_ref: str | None = None,
        transaction_id: str | int | None = None,
        event_type: str | None = None,
        provider_status: str | None = None,
    ) -> str:
        provider_event_id = (
            payload.get("webhook_id")
            or payload.get("event_id")
            or data.get("webhook_id")
            or data.get("event_id")
        )
        if provider_event_id:
            return str(provider_event_id)

        composite = "|".join(
            str(value or "")
            for value in (
                transaction_id or data.get("id") or data.get("transaction_id"),
                tx_ref or data.get("tx_ref") or data.get("txRef") or payload.get("tx_ref") or payload.get("txRef"),
                event_type or payload.get("type") or payload.get("event") or payload.get("event_type"),
                provider_status or data.get("status") or payload.get("status"),
                payload.get("created_at")
                or data.get("created_at")
                or hashlib.sha256(raw_body or repr(payload).encode("utf-8")).hexdigest(),
            )
        )
        if not composite.strip("|"):
            raise PaymentServiceError("Webhook event ID is missing")
        return "fw-" + hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def is_duplicate_webhook_event_error(
        self,
        error: IntegrityError,
        event_id: str | None,
    ) -> bool:
        if not event_id:
            return False
        original = getattr(error, "orig", None)
        constraint = getattr(getattr(original, "diag", None), "constraint_name", None)
        if constraint in {"payment_webhook_events_pkey", "payment_webhook_events_event_id_key"}:
            return True
        message = str(original or error).lower()
        return (
            "payment_webhook_events" in message
            and "event_id" in message
            and ("duplicate" in message or "unique" in message)
        )

    def ensure_user_can_view_payment(self, user: User | None, payment: Payment) -> None:
        if user is None:
            return
        role = user.role.strip().lower()
        if role == "admin":
            return
        if role == "farmer":
            farmer = self.db.scalar(select(Farmer).where(Farmer.user_id == user.user_id).limit(1))
            if farmer and farmer.farmer_id == payment.farmer_id:
                return
        if role in {"truck_provider", "transporter"}:
            linked = self.db.scalar(
                select(TripAllocation)
                .join(Truck, Truck.truck_id == TripAllocation.truck_id)
                .join(Transporter, Transporter.transporter_id == Truck.transporter_id)
                .where(
                    TripAllocation.allocation_id == payment.allocation_id,
                    Transporter.user_id == user.user_id,
                )
                .limit(1)
            )
            if linked:
                return
        if role == "hub_operator":
            linked = self.db.scalar(
                select(TripAllocation)
                .join(ColdHubAccount, ColdHubAccount.hub_id == TripAllocation.hub_id)
                .where(
                    TripAllocation.allocation_id == payment.allocation_id,
                    ColdHubAccount.user_id == user.user_id,
                )
                .limit(1)
            )
            if linked:
                return
        raise PaymentPermissionError("You do not have access to this payment")

    def payment_to_manager_dict(self, payment: Payment) -> dict:
        return {
            "payment_id": payment.payment_id,
            "allocation_id": payment.allocation_id,
            "farmer_id": payment.farmer_id,
            "payer_phone": payment.payer_phone,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "payment_status": payment.status,
            "status": payment.status,
            "purpose": payment.purpose,
            "payment_reference": payment.payment_reference,
            "flutterwave_ref": payment.flutterwave_ref,
            "tx_ref": payment.tx_ref,
            "payment_link": payment.payment_link,
        }

    def payment_to_dict(self, payment: Payment) -> dict:
        return {
            "payment_id": payment.payment_id,
            "allocation_id": payment.allocation_id,
            "farmer_id": payment.farmer_id,
            "payer_type": payment.payer_type,
            "payee_type": payment.payee_type,
            "payer_phone": payment.payer_phone,
            "payee_phone": payment.payee_phone,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "purpose": payment.purpose,
            "payment_method": payment.payment_method,
            "payment_status": payment.status,
            "status": payment.status,
            "payment_reference": payment.payment_reference,
            "flutterwave_ref": payment.flutterwave_ref,
            "tx_ref": payment.tx_ref,
            "transaction_id": payment.transaction_id,
            "payment_link": payment.payment_link,
            "provider_status": payment.provider_status,
            "created_at": payment.created_at,
            "verified_at": payment.verified_at,
            "failed_at": payment.failed_at,
            "paid_at": payment.paid_at,
            "refunded_at": payment.refunded_at,
            "settled_at": payment.settled_at,
            "last_checked_at": payment.last_checked_at,
        }
