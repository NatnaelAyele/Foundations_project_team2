from backend.database import fetch_one, execute_query

def save_forecast(farmer_id, quantity_kg, harvest_date, harvest_time):
    """
    Saves a new harvest forecast from the USSD menu into the database.
    PostgreSQL has no lastrowid, so the INSERT uses RETURNING to hand
    back the new forecast_id.
    """
    forecast_id = execute_query(
        """
        INSERT INTO harvest_forecasts (
            farmer_id,
            quantity_kg,
            harvest_date,
            harvest_time,
            status
        )
        VALUES (%s, %s, %s, %s, 'PENDING')
        RETURNING forecast_id
        """,
        (farmer_id, quantity_kg, harvest_date, harvest_time)
    )

    return get_forecast_by_id(forecast_id)


def get_forecast_by_id(forecast_id):
    """
    Gets one forecast by its ID.
    """
    return fetch_one(
        """
        SELECT forecast_id, farmer_id, quantity_kg, harvest_date,
               harvest_time, status, submitted_at, updated_at
        FROM harvest_forecasts
        WHERE forecast_id = %s
        """,
        (forecast_id,)
    )


def get_latest_forecast(farmer_id):
    """
    Gets the latest harvest forecast for one farmer.
    """
    return fetch_one(
        """
        SELECT forecast_id, farmer_id, quantity_kg, harvest_date,
               harvest_time, status, submitted_at, updated_at
        FROM harvest_forecasts
        WHERE farmer_id = %s
        ORDER BY submitted_at DESC
        LIMIT 1
        """,
        (farmer_id,)
    )


def get_latest_pending_forecast(farmer_id):
    """
    Gets the latest pending forecast.
    Only pending forecasts can be updated or cancelled by the farmer.
    """
    return fetch_one(
        """
        SELECT forecast_id, farmer_id, quantity_kg, harvest_date,
               harvest_time, status, submitted_at, updated_at
        FROM harvest_forecasts
        WHERE farmer_id = %s
          AND status = 'PENDING'
        ORDER BY submitted_at DESC
        LIMIT 1
        """,
        (farmer_id,)
    )


def update_forecast(forecast_id, quantity_kg, harvest_date, harvest_time):
    """
    Updates a pending harvest forecast
    """
    execute_query(
        """
        UPDATE harvest_forecasts
        SET quantity_kg = %s,
            harvest_date = %s,
            harvest_time = %s,
            status = 'PENDING'
        WHERE forecast_id = %s
          AND status = 'PENDING'
        """,
        (quantity_kg, harvest_date, harvest_time, forecast_id)
    )

    return get_forecast_by_id(forecast_id)


def cancel_forecast(forecast_id):
    """
    Cancels a pending harvest forecast.
    """
    execute_query(
        """
        UPDATE harvest_forecasts
        SET status = 'CANCELLED'
        WHERE forecast_id = %s
          AND status = 'PENDING'
        """,
        (forecast_id,)
    )

    return get_forecast_by_id(forecast_id)
