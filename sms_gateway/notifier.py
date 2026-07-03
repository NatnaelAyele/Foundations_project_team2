from datetime import datetime


# Sprint 1: stores simulated SMS notifications in memory.
# Future: replace this list with the notifications table in PostgreSQL.
SENT_NOTIFICATIONS = []


def send_notification(phone_number, message, notification_type="GENERAL", language="en"):
    """
    Simulates sending an SMS notification to a farmer.

    Sprint 1:
    - Stores the message in memory.
    - Prints the message in the terminal so we can see what the farmer receives.

    Future:
    - Save the message in the notifications table.
    - Send the real SMS through Africa's Talking.
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

    Tomato Logistics and phone numbers remain unchanged.
    Only labels such as From, To, Time, and Type are translated.
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

    print("\n========== SMS RECEIVED ==========")
    print(f"{from_label}: Tomato Logistics")
    print(f"{to_label}: {notification['phone_number']}")
    print(f"{time_label}: {notification['sent_at']}")
    print(f"{type_label}: {notification['notification_type']}")
    print("----------------------------------")
    print(notification["message"])
    print("==================================\n")


def get_sent_notifications(phone_number=None):
    """
    Returns simulated SMS notifications.

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
    Returns the latest SMS notifications for one farmer.

    We limit the number because USSD screens should stay short.
    """
    messages = get_sent_notifications(phone_number)
    return messages[-limit:]


def clear_notifications():
    """
    Clears all simulated SMS notifications before a fresh demo or test.
    """
    SENT_NOTIFICATIONS.clear()