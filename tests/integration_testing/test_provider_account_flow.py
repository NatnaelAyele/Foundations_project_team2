import pytest
from sqlalchemy import select

from backend.models.provider import ColdHub, ColdHubAccount, Transporter, Truck, User


def login(client, login_id):
    response = client.post(
        "/api/auth/login",
        json={"login_id": login_id, "password": "FreshLink!123"},
    )
    assert response.status_code == 200, response.text
    return response


def test_transporter_registration_login_and_truck_access(api_client, db_session, provider_payload):
    payload = provider_payload("truck_provider", 1)

    registration = api_client.post("/api/registrations/providers", json=payload)

    assert registration.status_code == 201, registration.text
    result = registration.json()
    user = db_session.get(User, result["user_id"])
    transporter = db_session.scalar(select(Transporter).where(Transporter.user_id == user.user_id))
    truck = db_session.get(Truck, result["truck_id"])
    assert user.role == "truck_provider"
    assert transporter is not None
    assert truck.transporter_id == transporter.transporter_id
    assert truck.status == "AVAILABLE"

    login_response = login(api_client, payload["username"])
    assert login_response.json()["dashboard_url"] == "/transporter_dashboard/transporter_dashboard.html"

    trucks = api_client.get("/api/transporter/trucks")
    assert trucks.status_code == 200
    assert trucks.json()["items"][0]["plate_number"] == "RAA 001A"


def test_hub_registration_login_and_capacity_update(api_client, db_session, provider_payload):
    payload = provider_payload("hub_operator", 2)

    registration = api_client.post("/api/registrations/providers", json=payload)

    assert registration.status_code == 201, registration.text
    result = registration.json()
    user = db_session.get(User, result["user_id"])
    account = db_session.scalar(select(ColdHubAccount).where(ColdHubAccount.user_id == user.user_id))
    hub = db_session.get(ColdHub, account.hub_id)
    assert user.role == "hub_operator"
    assert hub.available_capacity_kg == 2000

    login_response = login(api_client, payload["email"])
    assert login_response.json()["dashboard_url"] == "/storagehub_dashboard/hub_dashboard.html"

    update = api_client.patch(
        "/api/hub/capacity",
        json={"total_capacity_kg": 2500, "available_capacity_kg": 1800, "notes": "Morning update"},
    )
    assert update.status_code == 200, update.text
    assert update.json()["total_capacity_kg"] == 2500
    assert update.json()["available_capacity_kg"] == 1800

    db_session.refresh(hub)
    assert hub.total_capacity_kg == 2500
    assert hub.available_capacity_kg == 1800


def test_roles_cannot_access_another_provider_dashboard_api(api_client, provider_payload):
    hub_payload = provider_payload("hub_operator", 3)
    assert api_client.post("/api/registrations/providers", json=hub_payload).status_code == 201

    login(api_client, hub_payload["username"])
    transporter_response = api_client.get("/api/transporter/trucks")

    assert transporter_response.status_code == 403


def test_duplicate_provider_username_returns_conflict_without_second_user(api_client, db_session, provider_payload):
    payload = provider_payload("truck_provider", 4)
    assert api_client.post("/api/registrations/providers", json=payload).status_code == 201

    duplicate = api_client.post("/api/registrations/providers", json=payload)

    assert duplicate.status_code == 409
    assert db_session.scalars(select(User).where(User.username == payload["username"])).all().__len__() == 1
