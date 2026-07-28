from datetime import date

from sqlalchemy import func, select

from backend.auth.security import hash_password
from backend.models.operations import HarvestForecast
from backend.models.provider import User


def login_as_admin(client, db_session):
    admin = User(
        username="validation_admin",
        email="validation_admin@example.com",
        password_hash=hash_password("FreshLink!123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    response = client.post(
        "/api/auth/login",
        json={"login_id": admin.username, "password": "FreshLink!123"},
    )
    assert response.status_code == 200, response.text


def test_non_positive_forecast_quantity_is_rejected_without_forecast(api_client, db_session):
    login_as_admin(api_client, db_session)

    response = api_client.post(
        "/api/admin/forecasts",
        json={
            "farmer_id": 999,
            "quantity_kg": 0,
            "harvest_date": date.today().isoformat(),
            "needs_transport": True,
            "needs_storage": True,
        },
    )

    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(HarvestForecast)) == 0


def test_forecast_for_unknown_farmer_is_rejected_without_forecast(api_client, db_session):
    login_as_admin(api_client, db_session)

    response = api_client.post(
        "/api/admin/forecasts",
        json={
            "farmer_id": 999,
            "quantity_kg": 100,
            "harvest_date": date.today().isoformat(),
            "needs_transport": True,
            "needs_storage": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"
    assert db_session.scalar(select(func.count()).select_from(HarvestForecast)) == 0
