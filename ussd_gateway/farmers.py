# ussd_gateway/farmers.py

# Sprint 1: this file simulates registered farmers.
# Future: this file will connect to the farmers table in PostgreSQL.

REGISTERED_FARMERS = {
    "+250788000001": {
        "farmer_code": "001",
        "name": "Jean",
        "preferred_language": "en"
    },
    "+250788000002": {
        "farmer_code": "002",
        "name": "Aline",
        "preferred_language": "rw"
    }
}


def normalize_phone(phone_number):
    """
    Converts phone numbers into one standard format.

    Example:
    0788000001 becomes +250788000001

    This helps the system recognize the same farmer even if the
    phone number is typed in local format.
    """
    phone_number = phone_number.strip().replace(" ", "")

    if phone_number.startswith("0"):
        return "+250" + phone_number[1:]

    return phone_number


def get_farmer_by_phone(phone_number):
    """
    Finds a registered farmer using their phone number.

    Sprint 1:
    - Looks inside REGISTERED_FARMERS.

    Future:
    - Replace this with a database query:
      SELECT * FROM farmers WHERE phone = phone_number
    """
    phone_number = normalize_phone(phone_number)
    return REGISTERED_FARMERS.get(phone_number)