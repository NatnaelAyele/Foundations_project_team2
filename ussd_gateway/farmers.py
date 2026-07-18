# ussd_gateway/farmers.py

from backend.database import fetch_one


def normalize_phone(phone_number):
    """
    Converts local Rwanda phone numbers into international format.

    Example:
    0788000001 becomes +250788000001
    """
    phone_number = phone_number.strip().replace(" ", "")

    if phone_number.startswith("0"):
        return "+250" + phone_number[1:]

    return phone_number


def get_farmer_by_phone(phone_number):
    """
    Finds a registered farmer by phone number.

    This is the access check for USSD:
    - registered phone number = menu opens
    - unregistered phone number = access denied
    """
    phone_number = normalize_phone(phone_number)

    return fetch_one(
        """
        SELECT farmer_id, farmer_code, name, phone, preferred_language
        FROM farmers
        WHERE phone = %s
          AND is_active = TRUE
        """,
        (phone_number,)
    )