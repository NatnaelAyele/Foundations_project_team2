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
    Eg: 0788000001 becomes +250788000001
    """
    phone_number = phone_number.strip().replace(" ", "")

    if phone_number.startswith("0"):
        return "+250" + phone_number[1:]

    return phone_number


def get_farmer_by_phone(phone_number):
    """
    Finds a registered farmer using their phone number.
    This currently looks in the registered farmer list, 
    But in the future will be replaced with sql querries
    """
    phone_number = normalize_phone(phone_number)
    return REGISTERED_FARMERS.get(phone_number)