from sms_gateway.templates import (
    harvest_recorded_message,
    harvest_cancelled_message,
    trip_assigned_message,
    trip_cancelled_message
)
from sms_gateway.notifier import (
    send_notification,
    get_sent_notifications,
    clear_notifications
)


def sample_forecast():
    """
    Provides fake forecast data for SMS notification tests.
    """
    return {
        "quantity_kg": 300,
        "harvest_date": "2026-07-03",
        "harvest_time": "08:00"
    }


def sample_trip():
    """
    Provides fake trip data for future trip notification tests.
    """
    return {
        "quantity_kg": 300,
        "pickup_time": "2026-07-03 10:00",
        "truck_plate": "RAB 123A",
        "hub_name": "Kamonyi Hub A"
    }


def test_harvest_recorded_message():
    message = harvest_recorded_message(sample_forecast())

    assert "Harvest report recorded" in message
    assert "300" in message
    assert "pending coordination" in message


def test_harvest_cancelled_message():
    message = harvest_cancelled_message(sample_forecast())

    assert "Harvest report cancelled" in message
    assert "2026-07-03" in message


def test_trip_assigned_message():
    message = trip_assigned_message(sample_trip())

    assert "Pickup confirmed" in message
    assert "RAB 123A" in message
    assert "Kamonyi Hub A" in message


def test_trip_cancelled_message():
    message = trip_cancelled_message(sample_trip())

    assert "Pickup trip cancelled" in message
    assert "another update" in message


def test_send_notification_records_sms():
    clear_notifications()

    notification = send_notification(
        phone_number="+250788000001",
        message="Test notification",
        notification_type="TEST"
    )

    notifications = get_sent_notifications()

    assert notification["status"] == "SIMULATED"
    assert len(notifications) == 1
    assert notifications[0]["phone_number"] == "+250788000001"

def test_harvest_recorded_message_in_kinyarwanda():
    message = harvest_recorded_message(sample_forecast(), language="rw")

    assert "Raporo y'umusaruro yakiriwe" in message
    assert "300" in message
    assert "inyanya" in message


def test_harvest_cancelled_message_in_kinyarwanda():
    message = harvest_cancelled_message(sample_forecast(), language="rw")

    assert "Raporo y'umusaruro yasibwe" in message
    assert "2026-07-03" in message


def test_trip_assigned_message_in_kinyarwanda():
    message = trip_assigned_message(sample_trip(), language="rw")

    assert "Gufata umusaruro byemejwe" in message
    assert "RAB 123A" in message
    assert "Kamonyi Hub A" in message