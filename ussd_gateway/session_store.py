# Currently stores active sessions
# But in the future will be moved to Redis or databas
SESSIONS = {}

# Currently stores harvest forecast
# Will be moved to the db in the future
FORECASTS = []


def reset_state():
    """
    Clears all temporary demo data.
    Employed before making a new test or demo.
    """
    SESSIONS.clear()
    FORECASTS.clear()


def save_forecast(forecast):
    """
    Saves a new harvest forecast.
    """
    FORECASTS.append(forecast)
    return forecast


def get_latest_forecast(phone_number):
    """
    Gets the latest harvest forecast for one farmer.
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
    """
    forecast["quantity_kg"] = quantity_kg
    forecast["harvest_date"] = harvest_date
    forecast["harvest_time"] = harvest_time
    forecast["status"] = "pending"

    return forecast


def cancel_forecast(forecast):
    """
    Cancels a pending harvest forecast.
    """
    forecast["status"] = "cancelled"
    return forecast