def harvest_recorded_message(forecast, language="en"):
    """
    Builds the SMS sent after a farmer submits a new harvest report.
    """
    if language == "rw":
        return (
            "Raporo y'umusaruro yakiriwe.\n"
            f"Ingano: {forecast['quantity_kg']}kg z'inyanya\n"
            f"Itariki: {forecast['harvest_date']}\n"
            f"Igihe: {forecast['harvest_time']}\n"
            "Status: itegereje guhuza imodoka n'ububiko."
        )

    return (
        "Harvest report recorded.\n"
        f"Quantity: {forecast['quantity_kg']}kg tomatoes\n"
        f"Date: {forecast['harvest_date']}\n"
        f"Time: {forecast['harvest_time']}\n"
        "Status: pending coordination."
    )


def harvest_updated_message(forecast, language="en"):
    """
    Builds the SMS sent after a farmer updates a pending harvest report.
    """
    if language == "rw":
        return (
            "Raporo y'umusaruro yavuguruwe.\n"
            f"Ingano nshya: {forecast['quantity_kg']}kg z'inyanya\n"
            f"Itariki: {forecast['harvest_date']}\n"
            f"Igihe: {forecast['harvest_time']}\n"
            "Status: itegereje guhuza imodoka n'ububiko."
        )

    return (
        "Harvest report updated.\n"
        f"New quantity: {forecast['quantity_kg']}kg tomatoes\n"
        f"Date: {forecast['harvest_date']}\n"
        f"Time: {forecast['harvest_time']}\n"
        "Status: pending coordination."
    )


def harvest_cancelled_message(forecast, language="en"):
    """
    Builds the SMS sent after a farmer cancels a pending harvest report.
    """
    if language == "rw":
        return (
            "Raporo y'umusaruro yasibwe.\n"
            f"Ingano: {forecast['quantity_kg']}kg z'inyanya\n"
            f"Itariki: {forecast['harvest_date']}\n"
            f"Igihe: {forecast['harvest_time']}"
        )

    return (
        "Harvest report cancelled.\n"
        f"Quantity: {forecast['quantity_kg']}kg tomatoes\n"
        f"Date: {forecast['harvest_date']}\n"
        f"Time: {forecast['harvest_time']}"
    )


def trip_assigned_message(trip, language="en"):
    """
    Builds the SMS sent after the coordination engine assigns a pickup trip.
    This will be used later when trip allocation is connected.
    """
    if language == "rw":
        return (
            "Gufata umusaruro byemejwe.\n"
            f"Ingano: {trip['quantity_kg']}kg z'inyanya\n"
            f"Igihe cyo gufata: {trip['pickup_time']}\n"
            f"Imodoka: {trip['truck_plate']}\n"
            f"Ububiko: {trip['hub_name']}"
        )

    return (
        "Pickup confirmed.\n"
        f"Quantity: {trip['quantity_kg']}kg tomatoes\n"
        f"Pickup time: {trip['pickup_time']}\n"
        f"Truck: {trip['truck_plate']}\n"
        f"Storage hub: {trip['hub_name']}"
    )


def trip_cancelled_message(trip, language="en"):
    """
    Builds the SMS sent when an assigned pickup trip is cancelled.
    """
    if language == "rw":
        return (
            "Urugendo rwo gufata umusaruro rwasibwe.\n"
            f"Ingano: {trip['quantity_kg']}kg z'inyanya\n"
            f"Igihe: {trip['pickup_time']}\n"
            "Tegereza ubundi butumwa buvuye muri sisitemu."
        )

    return (
        "Pickup trip cancelled.\n"
        f"Quantity: {trip['quantity_kg']}kg tomatoes\n"
        f"Date: {trip['pickup_time']}\n"
        "Please wait for another update from the system."
    )