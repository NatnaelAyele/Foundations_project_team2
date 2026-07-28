from datetime import datetime
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.Flutterwave.payment import PaymentError, PaymentManager, PaymentStatus


class FakeGateway:
    def __init__(self, initialize_response=None, verify_response=None):
        self.initialize_response = initialize_response or {
            "status": "success",
            "payment_link": "https://payments.example.test/pay",
            "tx_ref": "FLW-TEST-001",
        }
        self.verify_response = verify_response or {"payment_status": "PAID"}

    def initialize_payment(self, payment):
        return self.initialize_response

    def verify_payment(self, tx_ref):
        return self.verify_response

    def refund_payment(self, tx_ref):
        return {"payment_status": "REFUNDED"}


class SilentLogger:
    def info(self, message):
        pass


def make_reservation(**overrides):
    reservation = {
        "status": "RESERVED",
        "allocation_id": 10,
        "farmer_id": 5,
        "truck_id": 2,
        "hub_id": 3,
        "total_load_kg": 100,
        "farmer_phone": "+250788000001",
        "hub_phone": "+250788000002",
        "forecasts": [{"farmer_id": 5, "forecast_id": 7, "quantity_kg": 100}],
    }
    reservation.update(overrides)
    return reservation


def test_payment_amount_is_calculated_from_transport_and_storage_rates():
    manager = PaymentManager(gateway=FakeGateway(), logger=SilentLogger())

    assert manager.calculate_transport_cost(make_reservation()) == 200
    assert manager.calculate_storage_cost(make_reservation()) == 100
    assert manager.calculate_total_amount(make_reservation()) == 300


def test_payment_requires_a_reserved_trip_with_positive_load():
    manager = PaymentManager(gateway=FakeGateway(), logger=SilentLogger())

    with pytest.raises(PaymentError, match="reserved trips"):
        manager.create_payment(make_reservation(status="PLANNED"))

    with pytest.raises(PaymentError, match="greater than 0"):
        manager.create_payment(make_reservation(total_load_kg=0))


def test_created_payment_is_pending_and_has_a_unique_reference():
    manager = PaymentManager(gateway=FakeGateway(), logger=SilentLogger())

    first = manager.create_payment(make_reservation())
    second = manager.create_payment(make_reservation())

    assert first["payment_status"] == PaymentStatus.PENDING
    assert first["amount"] == 300
    assert first["payment_reference"].startswith("TLP-10-")
    assert first["payment_reference"] != second["payment_reference"]


def test_verified_payment_is_marked_paid_with_a_timestamp():
    manager = PaymentManager(gateway=FakeGateway(), logger=SilentLogger())
    payment = manager.create_payment(make_reservation())

    verified = manager.verify_payment(payment)

    assert verified["payment_status"] == PaymentStatus.PAID
    assert isinstance(verified["paid_at"], datetime)
    assert verified["paid_at"] == verified["settled_at"]


def test_unsupported_payment_status_is_rejected():
    manager = PaymentManager(gateway=FakeGateway(), logger=SilentLogger())

    with pytest.raises(PaymentError, match="Unsupported payment status"):
        manager.update_payment_status({}, "UNKNOWN")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
