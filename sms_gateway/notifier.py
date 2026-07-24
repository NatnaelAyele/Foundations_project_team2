import os
import json
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from backend.database import execute_query, fetch_all

load_dotenv()

try:
    import africastalking
except ImportError:
    africastalking = None


_sms_client = None
DEFAULT_SMS_BASE_URL = "https://api.sandbox.africastalking.com/version1/messaging"


def normalize_sms_phone(phone_number):
    """
    Converts Rwanda phone numbers to the E.164 format Africa's Talking expects.
    """
    phone = str(phone_number).strip().replace(" ", "").replace("-", "")

    if phone.startswith("+"):
        return phone
    if phone.startswith("0"):
        return "+250" + phone[1:]
    if phone.startswith("250"):
        return "+" + phone

    return phone


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
    
    if not api_key:
        return None

    africastalking.initialize(username, api_key)
    _sms_client = africastalking.SMS

    return _sms_client


def get_sms_base_url():
    """
    Returns the HTTPS Africa's Talking SMS endpoint.
    """
    base_url = os.getenv("AT_SMS_BASE_URL", DEFAULT_SMS_BASE_URL).strip()
    parsed = urlparse(base_url)

    if parsed.scheme == "http" and parsed.port == 443:
        raise RuntimeError("AT_SMS_BASE_URL cannot use plain HTTP on port 443")
    if parsed.scheme != "https":
        raise RuntimeError("AT_SMS_BASE_URL must use https://")

    return base_url


def send_sms_over_https(phone_number, message, timeout=15):
    """
    Sends SMS directly to Africa's Talking over HTTPS.
    """
    username = os.getenv("AT_USERNAME", "sandbox")
    api_key = os.getenv("AT_API_KEY")

    if not api_key:
        raise RuntimeError("Africa's Talking SMS API key is not configured.")

    phone_number = normalize_sms_phone(phone_number)
    payload = urlencode(
        {
            "username": username,
            "to": phone_number,
            "message": message,
            "bulkSMSMode": 1,
        }
    ).encode("utf-8")

    request = Request(
        get_sms_base_url(),
        data=payload,
        headers={
            "Accept": "application/json",
            "apiKey": api_key,
            "User-Agent": "freshlink-sms/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            response_text = response.read().decode("utf-8")
            return json.loads(response_text)
    except HTTPError as error:
        response_text = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(response_text) from error


def send_sms_to_africas_talking(phone_number, message):
    """
    Sends SMS through Africa's Talking to the sandbox
    """
    phone_number = normalize_sms_phone(phone_number)

    return send_sms_over_https(phone_number, message)


def save_notification(farmer_id, phone_number, message, notification_type, language):
    """
    Inserts the content of the notification table row, and returns its id
    """
    phone_number = normalize_sms_phone(phone_number)

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
    Saves the data in the notification row, send the SMS though Africa's 
    Talking, and updates the delivery status in the thread background
    """
    notification_id = None
    phone_number = normalize_sms_phone(phone_number)

    # Action 1: Save the notification in the database
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

    # Action 2: Send the SMS
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
    Queues a notification and returns immediately to Africa's Talking so 
    that the notifications can later be saved in the backgorund to 
    prevent the farmer from waiting since sessions are timed
    """
    phone_number = normalize_sms_phone(phone_number)

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
