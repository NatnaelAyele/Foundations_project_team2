from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.Flutterwave.gateways.flutterwave import FlutterwaveGateway
from backend.database.connection import Base
from backend.models.operations import (
    ForecastAllocation,
    CoordinationPlan,
    HarvestForecast,
    Notification,
    Payment,
    PaymentWebhookEvent,
    TripAllocation,
)
from backend.models.provider import ColdHub, Farmer, Sector, Transporter, Truck, User
from backend.routes import payments as payment_routes
from backend.services.payment_service import (
    PaymentPermissionError,
    PaymentService,
    PaymentStatus,
)


def test_gateway_accepts_valid_webhook_signature():
    body = b'{"event":"charge.completed"}'
    secret = "freshlink-secret"
    gateway = FlutterwaveGateway(secret_key="sk", webhook_secret=secret)

    assert gateway.verify_webhook_signature(body, secret)


def test_gateway_rejects_invalid_webhook_signature():
    gateway = FlutterwaveGateway(secret_key="sk", webhook_secret="freshlink-secret")

    assert not gateway.verify_webhook_signature(b"{}", "invalid")


@pytest.mark.parametrize(
    ("provider_status", "expected"),
    [
        ("successful", "PAID"),
        ("failed", "FAILED"),
        ("cancelled", "CANCELLED"),
        ("pending", "PENDING"),
    ],
)
def test_gateway_maps_flutterwave_statuses(provider_status, expected):
    gateway = FlutterwaveGateway(secret_key="sk")

    assert gateway.map_transaction_status(provider_status) == expected


def test_gateway_default_callback_url_uses_app_base_url():
    gateway = FlutterwaveGateway(
        secret_key="sk",
        api_base_url="https://freshlink.example",
    )

    assert gateway.callback_url() == (
        "https://freshlink.example/api/payments/flutterwave/callback"
    )


class FakeGateway:
    def __init__(self):
        self.initialize_calls = 0
        self.verify_calls = 0
        self.payment_link = "https://pay.example/" + ("x" * 700)
        self.verify_status = "pending"
        self.transaction_id = None

    def initialize_payment(self, payment):
        self.initialize_calls += 1
        return {
            "status": "success",
            "payment_status": "INITIALIZED",
            "provider_status": "success",
            "payment_link": self.payment_link,
            "tx_ref": payment["tx_ref"],
            "raw_response": {"status": "success"},
        }

    def verify_payment(self, tx_ref, transaction_id=None):
        self.verify_calls += 1
        status_map = {
            "successful": PaymentStatus.PAID,
            "failed": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELLED,
            "pending": PaymentStatus.PENDING,
        }
        return {
            "payment_status": status_map[self.verify_status],
            "provider_status": self.verify_status,
            "tx_ref": tx_ref,
            "transaction_id": self.transaction_id,
            "flutterwave_ref": "flw-ref",
            "amount": 30,
            "currency": "RWF",
            "raw_response": {"status": self.verify_status},
        }

    def refund_payment(self, tx_ref, transaction_id=None, amount=None, reason=None):
        return {
            "payment_status": PaymentStatus.REFUNDED,
            "provider_status": "refunded",
            "tx_ref": tx_ref,
            "transaction_id": transaction_id,
            "raw_response": {"status": "success"},
        }

    def verify_webhook_signature(self, raw_body, signature):
        return signature == "valid"


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = Session()
    seed_payment_fixture(db)
    try:
        yield db
    finally:
        db.close()


def seed_payment_fixture(db):
    db.add_all(
        [
            User(user_id=1, username="farmer", password_hash="x", role="FARMER"),
            Sector(sector_id=1, name="Sector", district="District"),
            CoordinationPlan(plan_id=1, sector_id=1, status="COMPLETED"),
            Farmer(farmer_id=1, user_id=1, sector_id=1, name="Farmer", phone="0780000000"),
            Transporter(
                transporter_id=1,
                user_id=1,
                sector_id=1,
                name="Transporter",
                phone="0780000001",
            ),
            Truck(
                truck_id=1,
                transporter_id=1,
                plate_number="RAB 123A",
                capacity_kg=100,
                sector_id=1,
                status="BUSY",
            ),
            ColdHub(
                hub_id=1,
                sector_id=1,
                name="Hub",
                phone="0780000002",
                total_capacity_kg=1000,
                available_capacity_kg=900,
                operating_status="OPEN",
            ),
            TripAllocation(
                allocation_id=1,
                plan_id=1,
                truck_id=1,
                hub_id=1,
                sector_id=1,
                total_load_kg=10,
                status="SCHEDULED",
            ),
            HarvestForecast(forecast_id=1, farmer_id=1, quantity_kg=10, harvest_date=datetime(2026, 7, 17)),
            ForecastAllocation(allocation_id=1, forecast_id=1, allocated_quantity_kg=10),
        ]
    )
    db.commit()


def test_trip_start_requires_existing_paid_payment(db_session):
    service = PaymentService(db_session, gateway=FakeGateway())

    with pytest.raises(PaymentPermissionError):
        service.ensure_trip_can_start(1)


def test_trip_start_rejects_failed_payment(db_session):
    service = PaymentService(db_session, gateway=FakeGateway())
    payment = service.create_payment_record(1)
    payment.status = PaymentStatus.FAILED
    db_session.commit()

    with pytest.raises(PaymentPermissionError):
        service.ensure_trip_can_start(1)


def test_trip_start_allows_paid_payment(db_session):
    service = PaymentService(db_session, gateway=FakeGateway())
    payment = service.create_payment_record(1)
    payment.status = PaymentStatus.PAID
    db_session.commit()

    service.ensure_trip_can_start(1)


def test_failed_payment_reinitialization_creates_fresh_payment(db_session):
    gateway = FakeGateway()
    service = PaymentService(db_session, gateway=gateway)
    payment = service.create_payment_record(1)
    payment.status = PaymentStatus.FAILED
    db_session.commit()

    result = service.initialize_payment(1)

    assert result["payment_id"] != payment.payment_id
    assert result["status"] == PaymentStatus.INITIALIZED
    assert gateway.initialize_calls == 1


def test_duplicate_initialized_payment_is_reused(db_session):
    gateway = FakeGateway()
    service = PaymentService(db_session, gateway=gateway)

    first = service.initialize_payment(1)
    second = service.initialize_payment(1)

    assert second["payment_id"] == first["payment_id"]
    assert gateway.initialize_calls == 1


def test_initialize_existing_endpoint_persists_initialized_payment(db_session, monkeypatch):
    gateway = FakeGateway()
    service = PaymentService(db_session, gateway=gateway)
    payment = service.create_payment_record(1)
    db_session.commit()

    def payment_service_factory(db):
        return PaymentService(db, gateway=gateway)

    user = User(
        user_id=99,
        username="admin",
        password_hash="x",
        role="ADMIN",
    )
    monkeypatch.setattr(payment_routes, "PaymentService", payment_service_factory)

    response = payment_routes.initialize_existing_payment(
        payment_routes.ExistingPaymentInitializeRequest(payment_id=payment.payment_id),
        user=user,
        db=db_session,
    )
    db_session.expire_all()
    saved = db_session.get(Payment, payment.payment_id)

    assert response["payment_id"] == payment.payment_id
    assert saved.status == PaymentStatus.INITIALIZED
    assert saved.payment_link == gateway.payment_link
    assert saved.tx_ref
    assert saved.provider_response == {"status": "success"}


def test_callback_ignores_forged_cancelled_status_and_verifies(db_session):
    gateway = FakeGateway()
    service = PaymentService(db_session, gateway=gateway)
    payment = service.initialize_payment(1)

    result = service.process_callback(payment["tx_ref"], None, "cancelled")

    assert result["status"] == PaymentStatus.PENDING
    assert gateway.verify_calls == 1


@pytest.mark.parametrize(
    ("service_status", "redirect_status"),
    [
        (PaymentStatus.PAID, "success"),
        (PaymentStatus.PENDING, "pending"),
        (PaymentStatus.INITIALIZED, "pending"),
        (PaymentStatus.FAILED, "failed"),
        (PaymentStatus.CANCELLED, "failed"),
    ],
)
def test_callback_redirect_maps_verified_statuses(
    db_session,
    monkeypatch,
    service_status,
    redirect_status,
):
    class CallbackPaymentService:
        def __init__(self, db):
            pass

        def process_callback(self, tx_ref, transaction_id, provider_status):
            return {"status": service_status}

    monkeypatch.setattr(payment_routes, "PaymentService", CallbackPaymentService)

    response = payment_routes.flutterwave_callback("tx", "123", "successful", db_session)

    assert f"payment_status={redirect_status}" in response.headers["location"]


def test_missing_transaction_id_is_not_saved_as_string_none(db_session):
    gateway = FakeGateway()
    gateway.verify_status = "successful"
    service = PaymentService(db_session, gateway=gateway)
    payment = service.initialize_payment(1)

    service.verify_payment(payment_id=payment["payment_id"])
    saved = db_session.get(Payment, payment["payment_id"])

    assert saved.transaction_id is None


def test_duplicate_webhook_is_idempotent(db_session):
    gateway = FakeGateway()
    gateway.verify_status = "successful"
    gateway.transaction_id = "12345"
    service = PaymentService(db_session, gateway=gateway)
    payment = service.initialize_payment(1)
    payload = {
        "event_id": "evt-1",
        "type": "charge.completed",
        "data": {"tx_ref": payment["tx_ref"], "id": "12345", "status": "successful"},
    }

    first = service.process_webhook(b"{}", "valid", payload)
    second = service.process_webhook(b"{}", "valid", payload)

    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert db_session.scalar(select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_id == "evt-1"))


def test_flat_v3_webhook_payload_persists_metadata_and_payment_status(db_session):
    gateway = FakeGateway()
    gateway.verify_status = "successful"
    gateway.transaction_id = "10380986"
    service = PaymentService(db_session, gateway=gateway)
    payment = service.initialize_payment(1)
    payload = {
        "id": 10380986,
        "txRef": payment["tx_ref"],
        "event": "charge.completed",
        "status": "successful",
    }

    result = service.process_webhook(b'{"id":10380986}', "valid", payload)
    saved = db_session.get(Payment, payment["payment_id"])
    event = db_session.scalar(select(PaymentWebhookEvent))

    assert result["duplicate"] is False
    assert result["event_id"].startswith("fw-")
    assert saved.status == PaymentStatus.PAID
    assert saved.transaction_id == "10380986"
    assert saved.provider_status == "successful"
    assert saved.verified_at is not None
    assert event.event_type == "charge.completed"
    assert event.provider_status == "successful"


def test_flat_v3_webhook_duplicate_uses_composite_event_id(db_session):
    gateway = FakeGateway()
    gateway.verify_status = "successful"
    gateway.transaction_id = "10380986"
    service = PaymentService(db_session, gateway=gateway)
    payment = service.initialize_payment(1)
    payload = {
        "id": 10380986,
        "txRef": payment["tx_ref"],
        "event": "charge.completed",
        "status": "successful",
    }

    first = service.process_webhook(b'{"id":10380986}', "valid", payload)
    second = service.process_webhook(b'{"id":10380986}', "valid", payload)
    events = db_session.scalars(select(PaymentWebhookEvent)).all()

    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert first["event_id"] == second["event_id"]
    assert len(events) == 1


def test_payment_notification_keeps_full_payment_link(db_session):
    gateway = FakeGateway()
    service = PaymentService(db_session, gateway=gateway)

    service.initialize_payment(1)
    notification = db_session.scalar(select(Notification).order_by(Notification.notification_id.desc()))

    assert gateway.payment_link in notification.message


def test_integrity_error_filter_only_accepts_webhook_event_duplicates(db_session):
    service = PaymentService(db_session, gateway=FakeGateway())
    duplicate = IntegrityError(
        "insert",
        {},
        Exception("duplicate key value violates unique constraint payment_webhook_events event_id"),
    )
    unrelated = IntegrityError(
        "insert",
        {},
        Exception("duplicate key value violates unique constraint payments_tx_ref_key"),
    )

    assert service.is_duplicate_webhook_event_error(duplicate, "evt-1")
    assert not service.is_duplicate_webhook_event_error(unrelated, "evt-1")
