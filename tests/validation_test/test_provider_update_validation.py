from sqlalchemy import select

from backend.models.provider import ColdHub, Truck


def login(client, login_id):
    response = client.post(
        "/api/auth/login",
        json={"login_id": login_id, "password": "FreshLink!123"},
    )
    assert response.status_code == 200, response.text


def test_capacity_above_total_is_rejected_without_changing_hub(api_client, db_session, provider_payload):
    payload = provider_payload("hub_operator", 5)
    registration = api_client.post("/api/registrations/providers", json=payload)
    assert registration.status_code == 201
    login(api_client, payload["username"])
    hub = db_session.scalar(select(ColdHub))
    original_total = hub.total_capacity_kg
    original_available = hub.available_capacity_kg

    response = api_client.patch(
        "/api/hub/capacity",
        json={"total_capacity_kg": 1000, "available_capacity_kg": 1200},
    )

    assert response.status_code == 422
    db_session.refresh(hub)
    assert hub.total_capacity_kg == original_total
    assert hub.available_capacity_kg == original_available


def test_invalid_truck_status_is_rejected_without_changing_truck(api_client, db_session, provider_payload):
    payload = provider_payload("truck_provider", 6)
    registration = api_client.post("/api/registrations/providers", json=payload)
    assert registration.status_code == 201
    login(api_client, payload["username"])
    truck = db_session.scalar(select(Truck))
    original_status = truck.status

    response = api_client.patch(f"/api/transporter/trucks/{truck.truck_id}", json={"status": "FLYING"})

    assert response.status_code == 422
    db_session.refresh(truck)
    assert truck.status == original_status


def test_unauthenticated_provider_endpoint_is_rejected(api_client):
    response = api_client.get("/api/hub/capacity")

    assert response.status_code == 401


def test_wrong_provider_role_is_rejected(api_client, provider_payload):
    payload = provider_payload("hub_operator", 7)
    assert api_client.post("/api/registrations/providers", json=payload).status_code == 201
    login(api_client, payload["username"])

    response = api_client.get("/api/transporter/trucks")

    assert response.status_code == 403
