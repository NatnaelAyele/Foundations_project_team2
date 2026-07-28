from sqlalchemy import func, select

from backend.models.provider import User


def test_registration_with_missing_required_data_is_rejected_without_user(api_client, db_session, provider_payload):
    payload = provider_payload("truck_provider", 1)
    payload.pop("capacity_kg")

    response = api_client.post("/api/registrations/providers", json=payload)

    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


def test_registration_with_mismatched_passwords_is_rejected_without_user(api_client, db_session, provider_payload):
    payload = provider_payload("hub_operator", 2)
    payload["confirm_password"] = "Different!123"

    response = api_client.post("/api/registrations/providers", json=payload)

    assert response.status_code == 422
    assert "Passwords do not match" in response.text
    assert db_session.scalar(select(func.count()).select_from(User)) == 0


def test_duplicate_registration_returns_conflict_without_duplicate_user(api_client, db_session, provider_payload):
    payload = provider_payload("truck_provider", 3)
    assert api_client.post("/api/registrations/providers", json=payload).status_code == 201

    duplicate = api_client.post("/api/registrations/providers", json=payload)

    assert duplicate.status_code == 409
    user_count = db_session.scalar(
        select(func.count()).select_from(User).where(User.username == payload["username"])
    )
    assert user_count == 1


def test_login_with_wrong_password_is_rejected_without_authentication_cookie(api_client, provider_payload):
    payload = provider_payload("truck_provider", 4)
    assert api_client.post("/api/registrations/providers", json=payload).status_code == 201

    response = api_client.post(
        "/api/auth/login",
        json={"login_id": payload["username"], "password": "Incorrect!123"},
    )

    assert response.status_code == 401
    assert "freshlink_access_token" not in response.cookies


def test_login_with_missing_password_is_rejected(api_client):
    response = api_client.post("/api/auth/login", json={"login_id": "unknown"})

    assert response.status_code == 422
