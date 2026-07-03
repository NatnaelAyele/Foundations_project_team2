from ussd_gateway.ussd_app import handle_ussd
from ussd_gateway.session_store import reset_state, FORECASTS


def test_unregistered_phone_cannot_access_menu():
    reset_state()

    response = handle_ussd("+250788999999", "")

    assert response.startswith("END")
    assert "not registered" in response


def test_registered_phone_can_open_language_menu():
    reset_state()

    response = handle_ussd("+250788000001", "")

    assert response.startswith("CON")
    assert "English" in response
    assert "Kinyarwanda" in response


def test_harvest_report_flow():
    reset_state()
    phone = "+250788000001"

    handle_ussd(phone, "")
    handle_ussd(phone, "1")
    handle_ussd(phone, "1")
    handle_ussd(phone, "300")
    handle_ussd(phone, "2026-07-03")
    handle_ussd(phone, "08:00")
    response = handle_ussd(phone, "1")

    assert response.startswith("END")
    assert len(FORECASTS) == 1
    assert FORECASTS[0]["quantity_kg"] == 300
    assert FORECASTS[0]["status"] == "pending"


def test_cancel_pending_harvest_report():
    reset_state()
    phone = "+250788000001"

    handle_ussd(phone, "")
    handle_ussd(phone, "1")
    handle_ussd(phone, "1")
    handle_ussd(phone, "300")
    handle_ussd(phone, "2026-07-03")
    handle_ussd(phone, "08:00")
    handle_ussd(phone, "1")

    handle_ussd(phone, "")
    handle_ussd(phone, "1")
    handle_ussd(phone, "3")
    response = handle_ussd(phone, "1")

    assert response.startswith("END")
    assert FORECASTS[-1]["status"] == "cancelled"