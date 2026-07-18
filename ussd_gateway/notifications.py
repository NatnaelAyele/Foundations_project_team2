# ussd_gateway/notifications.py

from sms_gateway.notifier import send_notification
from sms_gateway.templates import (
    harvest_recorded_message,
    harvest_updated_message,
    harvest_cancelled_message
)


def notify_harvest_recorded(farmer, forecast, language="en"):
    """
    Sends SMS after a harvest report is submitted.
    """
    message = harvest_recorded_message(forecast, language)

    return send_notification(
        farmer_id=farmer["farmer_id"],
        phone_number=farmer["phone"],
        message=message,
        notification_type="HARVEST_RECORDED",
        language=language
    )


def notify_harvest_updated(farmer, forecast, language="en"):
    """
    Sends SMS after a harvest report is updated.
    """
    message = harvest_updated_message(forecast, language)

    return send_notification(
        farmer_id=farmer["farmer_id"],
        phone_number=farmer["phone"],
        message=message,
        notification_type="HARVEST_UPDATED",
        language=language
    )


def notify_harvest_cancelled(farmer, forecast, language="en"):
    """
    Sends SMS after a harvest report is cancelled.
    """
    message = harvest_cancelled_message(forecast, language)

    return send_notification(
        farmer_id=farmer["farmer_id"],
        phone_number=farmer["phone"],
        message=message,
        notification_type="HARVEST_CANCELLED",
        language=language
    )