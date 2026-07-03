from datetime import datetime


# Sprint 1: stores simulated SMS notifications in memory.
# Future: the list will be replaced with the notifications table in PostgreSQL.
SENT_NOTIFICATIONS = []

def send_notification(phone_number, message, notification_type="GENERAL", language="en"):
    """
    Simulation of how notifications will be sent and stored
    """
    notification = {
        "phone_number": phone_number,
        "message": message,
        "notification_type": notification_type,
        "language": language,
        "status": "SIMULATED",
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    SENT_NOTIFICATIONS.append(notification)
    print_received_notification(notification)

    return notification


def print_received_notification(notification):
    """
    Prints one SMS notification in the farmer's selected language.
    """
    language = notification.get("language", "en")

    if language == "rw":
        from_label = "Ivuye kuri"
        to_label = "Kuri"
        time_label = "Igihe"
        type_label = "Ubwoko"
    else:
        from_label = "From"
        to_label = "To"
        time_label = "Time"
        type_label = "Type"

    print("\n========== SMS NOTIFICATION ===========")
    print(f"{from_label}: Tomato Logistics")
    print(f"{to_label}: {notification['phone_number']}")
    print(f"{time_label}: {notification['sent_at']}")
    print(f"{type_label}: {notification['notification_type']}")
    print("----------------------------------------")
    print(notification["message"])
    print("========================================\n")


def get_sent_notifications(phone_number=None):
    """
    If phone_number is provided, only messages for that farmer are returned.
    """
    if phone_number is None:
        return SENT_NOTIFICATIONS

    return [
        notification for notification in SENT_NOTIFICATIONS
        if notification["phone_number"] == phone_number
    ]


def get_recent_notifications(phone_number, limit=3):
    """
    Returns the latest SMS notifications for one farmer due to small phone screen
    """
    messages = get_sent_notifications(phone_number)
    return messages[-limit:]


def clear_notifications():
    """
    Clears all simulated SMS notifications before a new test is done.
    """
    SENT_NOTIFICATIONS.clear()