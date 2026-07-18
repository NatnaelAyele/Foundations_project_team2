# ussd_gateway/ussd_app.py

from datetime import datetime

from sms_gateway.notifier import get_recent_notifications
from ussd_gateway.farmers import get_farmer_by_phone, normalize_phone
from ussd_gateway.forecast_repository import (
    save_forecast,
    get_latest_forecast,
    get_latest_pending_forecast,
    update_forecast,
    cancel_forecast
)
from ussd_gateway.session_store import SESSIONS
from ussd_gateway.menus import (
    language_menu,
    main_menu,
    quantity_prompt,
    date_prompt,
    time_prompt,
    confirm_harvest_message,
    submitted_message,
    updated_message,
    cancelled_message,
    help_menu,
    invalid_choice,
    invalid_quantity,
    invalid_date,
    invalid_time
)
from ussd_gateway.notifications import (
    notify_harvest_recorded,
    notify_harvest_updated,
    notify_harvest_cancelled
)


def continue_session(message):
    """
    Keeps the USSD session open.
    Africa's Talking expects continuing responses to start with CON.
    """
    return "CON " + message


def end_session(session_key, message):
    """
    Ends the USSD session.
    Africa's Talking expects final responses to start with END.
    """
    SESSIONS.pop(session_key, None)
    return "END " + message


def handle_ussd(phone_number, message, session_id=None):
    """
    Main USSD controller.

    Terminal demo and FastAPI both call this same function.
    FastAPI passes session_id from Africa's Talking.
    """
    phone_number = normalize_phone(phone_number)
    message = message.strip()
    session_key = session_id or phone_number

    farmer = get_farmer_by_phone(phone_number)

    if farmer is None:
        return end_session(
            session_key,
            "Your phone number is not registered. Please contact the admin."
        )

    if session_key not in SESSIONS:
        SESSIONS[session_key] = {
            "step": "LANGUAGE",
            "farmer": farmer,
            "language": farmer.get("preferred_language", "en")
        }
        return continue_session(language_menu())

    session = SESSIONS[session_key]

    if message == "0":
        return end_session(session_key, exit_message(session["language"]))

    step = session["step"]

    if step == "LANGUAGE":
        return handle_language(session_key, message)

    if step == "MAIN":
        return handle_main_menu(session_key, message)

    if step == "INFO_SCREEN":
        return handle_info_screen(session_key, message)

    if step == "ASK_QUANTITY":
        return handle_quantity(session_key, message)

    if step == "ASK_DATE":
        return handle_date(session_key, message)

    if step == "ASK_TIME":
        return handle_time(session_key, message)

    if step == "CONFIRM_HARVEST":
        return handle_harvest_confirmation(session_key, message)

    if step == "CONFIRM_CANCEL":
        return handle_cancel_confirmation(session_key, message)

    return end_session(session_key, "Something went wrong. Please try again.")


def exit_message(language):
    """
    Returns exit message in selected language.
    """
    return "Murakoze gukoresha FreshLink." if language == "rw" else "Thank you for using FreshLink."


def handle_language(session_key, choice):
    """
    Saves the farmer language choice.
    """
    session = SESSIONS[session_key]

    if choice == "1":
        session["language"] = "en"
    elif choice == "2":
        session["language"] = "rw"
    else:
        return continue_session("Invalid choice.\n" + language_menu())

    session["step"] = "MAIN"
    return continue_session(main_menu(session["farmer"], session["language"]))


def handle_main_menu(session_key, choice):
    """
    Handles farmer main menu options.
    """
    session = SESSIONS[session_key]
    language = session["language"]

    if choice == "1":
        return start_create_flow(session_key)

    if choice == "2":
        return show_info_screen(session_key, pickup_status(session["farmer"], language))

    if choice == "3":
        return start_update_flow(session_key)

    if choice == "4":
        return start_cancel_flow(session_key)

    if choice == "5":
        return show_info_screen(session_key, sms_messages_screen(session["farmer"], language))

    if choice == "6":
        return show_info_screen(session_key, help_menu(language))

    if choice == "7":
        session["step"] = "LANGUAGE"
        return continue_session(language_menu())

    return continue_session(invalid_choice(language) + "\n" + main_menu(session["farmer"], language))


def show_info_screen(session_key, content):
    """
    Shows read-only screens such as status, SMS inbox, and help.
    """
    session = SESSIONS[session_key]
    language = session["language"]
    session["step"] = "INFO_SCREEN"

    if language == "rw":
        return continue_session(content + "\n\n9. Subira inyuma\n0. Sohoka")

    return continue_session(content + "\n\n9. Back\n0. Exit")


def handle_info_screen(session_key, choice):
    """
    Lets the farmer return from read-only screens.
    """
    session = SESSIONS[session_key]
    language = session["language"]

    if choice == "9":
        session["step"] = "MAIN"
        return continue_session(main_menu(session["farmer"], language))

    return continue_session(invalid_choice(language) + "\n\n9. Back\n0. Exit")


def clear_harvest_draft(session):
    """
    Clears temporary harvest values from the current USSD session.
    """
    session.pop("quantity_kg", None)
    session.pop("harvest_date", None)
    session.pop("harvest_time", None)
    session.pop("target_forecast", None)


def start_create_flow(session_key):
    """
    Starts a new harvest report.
    """
    session = SESSIONS[session_key]
    clear_harvest_draft(session)

    session["action"] = "CREATE"
    session["step"] = "ASK_QUANTITY"

    return continue_session(quantity_prompt(session["language"]))


def start_update_flow(session_key):
    """
    Starts updating the latest pending harvest report.
    """
    session = SESSIONS[session_key]
    language = session["language"]
    farmer = session["farmer"]

    latest = get_latest_pending_forecast(farmer["farmer_id"])

    if latest is None:
        message = "No pending harvest report found." if language == "en" else "Nta raporo itegereje yabonetse."
        return show_info_screen(session_key, message)

    clear_harvest_draft(session)
    session["action"] = "UPDATE"
    session["target_forecast"] = latest
    session["step"] = "ASK_QUANTITY"

    return continue_session(quantity_prompt(language))


def handle_quantity(session_key, text):
    """
    Validates harvest quantity and moves to date entry.
    """
    session = SESSIONS[session_key]
    language = session["language"]

    if text == "9":
        session["step"] = "MAIN"
        return continue_session(main_menu(session["farmer"], language))

    try:
        quantity_kg = float(text)
    except ValueError:
        return continue_session(invalid_quantity(language))

    if quantity_kg <= 0:
        return continue_session(invalid_quantity(language))

    session["quantity_kg"] = quantity_kg
    session["step"] = "ASK_DATE"

    return continue_session(date_prompt(language))


def handle_date(session_key, text):
    """
    Validates harvest date and moves to time entry.
    """
    session = SESSIONS[session_key]
    language = session["language"]

    if text == "9":
        session["step"] = "ASK_QUANTITY"
        return continue_session(quantity_prompt(language))

    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return continue_session(invalid_date(language))

    session["harvest_date"] = text
    session["step"] = "ASK_TIME"

    return continue_session(time_prompt(language))


def handle_time(session_key, text):
    """
    Validates harvest time and moves to confirmation.
    """
    session = SESSIONS[session_key]
    language = session["language"]

    if text == "9":
        session["step"] = "ASK_DATE"
        return continue_session(date_prompt(language))

    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        return continue_session(invalid_time(language))

    session["harvest_time"] = text
    session["step"] = "CONFIRM_HARVEST"

    return continue_session(confirm_harvest_message(session))


def handle_harvest_confirmation(session_key, choice):
    """
    Saves or updates the harvest forecast after farmer confirmation.
    """
    session = SESSIONS[session_key]
    language = session["language"]
    farmer = session["farmer"]
    action = session.get("action", "CREATE")

    if choice == "9":
        session["step"] = "ASK_TIME"
        return continue_session(time_prompt(language))

    if choice != "1":
        return continue_session(invalid_choice(language))

    if action == "UPDATE":
        target = session["target_forecast"]

        forecast = update_forecast(
            target["forecast_id"],
            session["quantity_kg"],
            session["harvest_date"],
            session["harvest_time"]
        )

        notify_harvest_updated(farmer, forecast, language)
        return end_session(session_key, updated_message(language))

    forecast = save_forecast(
        farmer["farmer_id"],
        session["quantity_kg"],
        session["harvest_date"],
        session["harvest_time"]
    )

    notify_harvest_recorded(farmer, forecast, language)
    return end_session(session_key, submitted_message(language))


def pickup_status(farmer, language):
    """
    Shows the latest harvest report status.
    """
    latest = get_latest_forecast(farmer["farmer_id"])

    if latest is None:
        return "No harvest report found." if language == "en" else "Nta raporo yabonetse."

    if language == "rw":
        return (
            "Raporo iheruka:\n"
            f"Ingano: {latest['quantity_kg']}kg\n"
            f"Itariki: {latest['harvest_date']}\n"
            f"Igihe: {str(latest['harvest_time'])[:5]}\n"
            f"Status: {latest['status']}"
        )

    return (
        "Latest harvest report:\n"
        f"Quantity: {latest['quantity_kg']}kg tomatoes\n"
        f"Date: {latest['harvest_date']}\n"
        f"Time: {str(latest['harvest_time'])[:5]}\n"
        f"Status: {latest['status']}"
    )


def sms_messages_screen(farmer, language):
    """
    Shows the last three SMS messages inside the USSD menu.
    """
    messages = get_recent_notifications(farmer["farmer_id"], limit=3)

    if not messages:
        return "No SMS messages found." if language == "en" else "Nta SMS ziraboneka."

    title = "Latest SMS messages:" if language == "en" else "SMS ziheruka:"
    lines = [title]

    for index, notification in enumerate(messages, start=1):
        short_message = notification["message"].replace("\n", " ")

        if len(short_message) > 90:
            short_message = short_message[:90] + "..."

        lines.append(f"{index}. {notification['notification_type']} - {short_message}")

    return "\n".join(lines)


def start_cancel_flow(session_key):
    """
    Starts cancellation for the latest pending forecast.
    """
    session = SESSIONS[session_key]
    language = session["language"]
    farmer = session["farmer"]

    latest = get_latest_pending_forecast(farmer["farmer_id"])

    if latest is None:
        message = "No pending harvest report found." if language == "en" else "Nta raporo itegereje yabonetse."
        return show_info_screen(session_key, message)

    session["step"] = "CONFIRM_CANCEL"
    session["cancel_forecast"] = latest

    if language == "rw":
        return continue_session(
            "Siba raporo iheruka?\n"
            f"Ingano: {latest['quantity_kg']}kg\n"
            f"Itariki: {latest['harvest_date']}\n\n"
            "1. Emeza gusiba\n"
            "9. Subira inyuma\n"
            "0. Sohoka"
        )

    return continue_session(
        "Cancel latest harvest report?\n"
        f"Quantity: {latest['quantity_kg']}kg tomatoes\n"
        f"Date: {latest['harvest_date']}\n\n"
        "1. Confirm cancel\n"
        "9. Back\n"
        "0. Exit"
    )


def handle_cancel_confirmation(session_key, choice):
    """
    Cancels the latest pending forecast.
    """
    session = SESSIONS[session_key]
    language = session["language"]
    farmer = session["farmer"]

    if choice == "9":
        session["step"] = "MAIN"
        return continue_session(main_menu(farmer, language))

    if choice != "1":
        return continue_session(invalid_choice(language))

    target = session["cancel_forecast"]
    forecast = cancel_forecast(target["forecast_id"])

    notify_harvest_cancelled(farmer, forecast, language)
    return end_session(session_key, cancelled_message(language))