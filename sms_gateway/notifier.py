import os
from threading import Thread

from dotenv import load_dotenv

from backend.database import execute_query, fetch_all

load_dotenv()

try:
    import africastalking
except ImportError:
    africastalking = None


_sms_client = None


def get_sms_client():
    """
    Creates the Africa's Talking SMS client once.
    """
    global _sms_client

    if _sms_client is not None:
        return _sms_client

    if africastalking is None:
        return None

    username = os.getenv("AT_USERNAME", "sandbox")
    api_key = os.getenv("AT_API_KEY")

    print(f"--- DEBUG AT_USERNAME: {username} ---")
    print(f"--- DEBUG AT_API_KEY: {api_key} ---")
    
    if not api_key:
        return None

    africastalking.initialize(username, api_key)
    _sms_client = africastalking.SMS

    return _sms_client


def send_sms_to_africas_talking(phone_number, message):
    """
    Sends SMS through Africa's Talking to the sandbox
    """
    sms_client = get_sms_client()

    if sms_client is None:
        raise RuntimeError("Africa's Talking SMS client is not configured.")

    return sms_client.send(message, [phone_number])


def save_notification(farmer_id, phone_number, message, notification_type, language):
    """
    Inserts the content of the notification table row, and returns its id
    """
    return execute_query(
        """
        INSERT INTO notifications (
            farmer_id,
            recipient_phone,
            channel,
            notification_type,
            message,
            language,
            status
        )
        VALUES (%s, %s, 'SMS', %s, %s, %s, 'pending')
        RETURNING notification_id
        """,
        (farmer_id, phone_number, notification_type, message, language)
    )


def update_notification_status(notification_id, status):
    """
    Updates SMS delivery status without crashing anything.
    """
    if not notification_id:
        return

    try:
        execute_query(
            """
            UPDATE notifications
            SET status = %s
            WHERE notification_id = %s
            """,
            (status, notification_id)
        )
    except Exception as error:
        print("\n========== NOTIFICATION STATUS UPDATE ERROR ==========")
        print(error)
        print("======================================================\n")


def process_notification_in_background(farmer_id, phone_number, message, notification_type, language):
    """
    Does ALL the slow work off the USSD request thread:

    1. saves the notification row
    2. sends the SMS through Africa's Talking
    3. updates the delivery status

    Nothing here can delay or break the USSD screen the farmer sees.
    """
    notification_id = None

    # 1. save to database
    try:
        notification_id = save_notification(
            farmer_id, phone_number, message, notification_type, language
        )
        print(f"Notification {notification_id} saved for {phone_number}.")
    except Exception as error:
        print("\n========== SAVE NOTIFICATION ERROR ==========")
        print(error)
        print("=============================================\n")
        return

    # 2. send SMS
    sms_enabled = os.getenv("AT_SMS_ENABLED", "false").lower() == "true"

    if not sms_enabled:
        print("SMS gateway disabled (AT_SMS_ENABLED=false). Notification saved only.")
        return

    try:
        provider_response = send_sms_to_africas_talking(phone_number, message)
        update_notification_status(notification_id, "sent")

        print("\n========== AFRICA'S TALKING SMS SENT ==========")
        print(provider_response)
        print("===============================================\n")

    except Exception as error:
        update_notification_status(notification_id, "failed")

        print("\n========== AFRICA'S TALKING SMS ERROR ==========")
        print(error)
        print("================================================\n")


def send_notification(farmer_id, phone_number, message, notification_type, language="en"):
    """
    Queues a notification and returns immediately.

    IMPORTANT: this does no database work on the calling thread.
    The USSD response must go back to Africa's Talking within a few
    seconds or the farmer sees a network error, so everything slow
    happens in a background thread.
    """
    Thread(
        target=process_notification_in_background,
        args=(farmer_id, phone_number, message, notification_type, language),
        daemon=True
    ).start()

    return {
        "farmer_id": farmer_id,
        "recipient_phone": phone_number,
        "notification_type": notification_type,
        "message": message,
        "language": language,
        "status": "queued"
    }


def get_recent_notifications(farmer_id, limit=3):
    """
    Gets the newest SMS messages for USSD display.
    """
    return fetch_all(
        """
        SELECT notification_id, farmer_id, recipient_phone, notification_type,
               message, language, status, sent_time
        FROM notifications
        WHERE farmer_id = %s
        ORDER BY sent_time DESC
        LIMIT %s
        """,
        (farmer_id, limit)
    )


def get_all_notifications(farmer_id):
    """
    Gets all SMS messages for dashboard or admin display.
    """
    return fetch_all(
        """
        SELECT notification_id, farmer_id, recipient_phone, notification_type,
               message, language, status, sent_time
        FROM notifications
        WHERE farmer_id = %s
        ORDER BY sent_time DESC
        """,
        (farmer_id,)
    )