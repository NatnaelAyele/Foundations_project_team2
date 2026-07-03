# Sprint 1: stores active USSD sessions in memory.
# Future: this can move to Redis or a database session table.
SESSIONS = {}

# Sprint 1: stores harvest reports in memory.
# Future: this will become the harvest_forecasts table.
FORECASTS = []


def reset_state():
    """
    Clears all temporary demo data.
    Used before tests or fresh simulations.
    """
    SESSIONS.clear()
    FORECASTS.clear()


def save_forecast(forecast):
    """
    Saves a new harvest forecast.

    Future database connection:
    Replace this with INSERT INTO harvest_forecasts.
    """
    FORECASTS.append(forecast)
    return forecast


def get_latest_forecast(phone_number):
    """
    Gets the latest harvest forecast for one farmer.

    Future database connection:
    Replace this with SELECT latest forecast WHERE phone_number = ...
    """
    farmer_forecasts = [
        forecast for forecast in FORECASTS
        if forecast["phone_number"] == phone_number
    ]

    if not farmer_forecasts:
        return None

    return farmer_forecasts[-1]


def update_forecast(forecast, quantity_kg, harvest_date, harvest_time):
    """
    Updates a pending harvest forecast.

    Farmers may harvest more or less than expected, so this allows them
    to correct the quantity, date, or time before coordination happens.
    """
    forecast["quantity_kg"] = quantity_kg
    forecast["harvest_date"] = harvest_date
    forecast["harvest_time"] = harvest_time
    forecast["status"] = "pending"

    return forecast


def cancel_forecast(forecast):
    """
    Cancels a pending harvest forecast.

    Only pending reports should be cancelled through USSD.
    Allocated trips should be handled by the admin.
    """
    forecast["status"] = "cancelled"
    return forecast