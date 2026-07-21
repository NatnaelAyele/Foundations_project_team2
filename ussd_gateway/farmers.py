from backend.database import fetch_one


def normalize_phone(phone_number):
    """
    Converts local Rwanda phone numbers into international format.
    0788000001 becomes +250788000001
    """
    phone_number = phone_number.strip().replace(" ", "").replace("-", "")

    if phone_number.startswith("0"):
        return "+250" + phone_number[1:]
    if phone_number.startswith("250"):
        return "+" + phone_number

    return phone_number


def phone_lookup_candidates(phone_number):
    """
    Returns every canonical format used by existing FreshLink data.
    """
    normalized = normalize_phone(phone_number)
    candidates = [normalized]

    if normalized.startswith("+250"):
        candidates.append("0" + normalized[4:])

    return list(dict.fromkeys(candidates))


def get_farmer_by_phone(phone_number):
    """
    Finds a registered farmer by phone number to give access
    """
    phone_numbers = phone_lookup_candidates(phone_number)

    return fetch_one(
        """
        SELECT farmer_id, farmer_code, name, phone, preferred_language
        FROM farmers
        WHERE phone = ANY(%s)
          AND is_active = TRUE
        """,
        (phone_numbers,)
    )
