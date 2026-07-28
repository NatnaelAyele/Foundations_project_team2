import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.routes.accounts import ProviderRegistration


def registration_data(**overrides):
    data = {
        "role": "truck_provider",
        "username": "truckowner",
        "email": "truck@example.com",
        "password": "FreshLink!123",
        "confirm_password": "FreshLink!123",
        "name": "Truck Owner",
        "phone": "0788000001",
        "district": "Kamonyi",
        "sector": "Runda",
        "cell": "Gacurabwenge",
        "village": "Kigusa",
        "plate_number": "RAA 001A",
        "capacity_kg": 1000,
    }
    data.update(overrides)
    return data


def test_truck_provider_registration_accepts_complete_data():
    registration = ProviderRegistration(**registration_data())

    assert registration.role == "truck_provider"
    assert registration.plate_number == "RAA 001A"
    assert registration.capacity_kg == 1000


def test_hub_registration_requires_total_capacity():
    data = registration_data(role="hub_operator", plate_number=None, capacity_kg=None)

    with pytest.raises(ValidationError, match="total_capacity_kg"):
        ProviderRegistration(**data)


def test_truck_registration_requires_plate_number_and_capacity():
    with pytest.raises(ValidationError, match="plate_number"):
        ProviderRegistration(**registration_data(plate_number=None))

    with pytest.raises(ValidationError, match="capacity_kg"):
        ProviderRegistration(**registration_data(capacity_kg=None))


def test_registration_rejects_mismatched_passwords():
    with pytest.raises(ValidationError, match="Passwords do not match"):
        ProviderRegistration(**registration_data(confirm_password="Different!123"))


def test_registration_rejects_non_positive_capacity():
    with pytest.raises(ValidationError):
        ProviderRegistration(**registration_data(capacity_kg=0))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
