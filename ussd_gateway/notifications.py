from sms_gateway.notifier import send_notification
from sms_gateway.templates import (
    harvest_recorded_message,
    harvest_updated_message,
    harvest_cancelled_message
)


def notify_harvest_recorded(phone_number, forecast, language="en"):
    """
    Sends SMS message after a new harvest report is submitted through USSD.
    """
    message = harvest_recorded_message(forecast, language)

    return send_notification(
        phone_number=phone_number,
        message=message,
        notification_type="HARVEST_RECORDED",
        language=language
    )


def notify_harvest_updated(phone_number, forecast, language="en"):
    """
    Sends SMS message after a farmer updates a pending harvest report.
    """
    message = harvest_updated_message(forecast, language)

    return send_notification(
        phone_number=phone_number,
        message=message,
        notification_type="HARVEST_UPDATED",
        language=language
    )


def notify_harvest_cancelled(phone_number, forecast, language="en"):
    """
    Sends SMS message after a pending harvest report is cancelled.
    """
    message = harvest_cancelled_message(forecast, language)

    return send_notification(
        phone_number=phone_number,
        message=message,
        notification_type="HARVEST_CANCELLED",
        language=language
    )