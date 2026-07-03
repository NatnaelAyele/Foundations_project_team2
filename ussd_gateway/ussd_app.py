from datetime import datetime

from sms_gateway.notifier import get_recent_notifications
from ussd_gateway.farmers import get_farmer_by_phone, normalize_phone
from ussd_gateway.session_store import (
    SESSIONS,
    save_forecast,
    get_latest_forecast,
    update_forecast,
    cancel_forecast
)
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


def end_session(phone_number, message):
    """
    Ends a USSD session and clears temporary session progress.
    """
    SESSIONS.pop(phone_number, None)
    return "END " + message


def continue_session(message):
    """
    Keeps a USSD session open for the next farmer reply.
    """
    return "CON " + message


def handle_ussd(phone_number, message):
    """
    Main USSD entry point.

    Future API connection:
    A Flask route or Africa's Talking callback will call this function
    with phone_number and message.
    """
    phone_number = normalize_phone(phone_number)
    message = message.strip()

    farmer = get_farmer_by_phone(phone_number)

    if farmer is None:
        return end_session(
            phone_number,
            "Your phone number is not registered. Please contact the admin."
        )

    if phone_number not in SESSIONS:
        SESSIONS[phone_number] = {
            "step": "LANGUAGE",
            "farmer": farmer,
            "language": farmer.get("preferred_language", "en")
        }
        return continue_session(language_menu())

    session = SESSIONS[phone_number]

    if message == "0":
        return end_session(phone_number, "Thank you for using Tomato Logistics.")

    step = session["step"]

    if step == "LANGUAGE":
        return handle_language(phone_number, message)

    if step == "MAIN":
        return handle_main_menu(phone_number, message)

    if step == "INFO_SCREEN":
        return handle_info_screen(phone_number, message)

    if step == "ASK_QUANTITY":
        return handle_quantity(phone_number, message)

    if step == "ASK_DATE":
        return handle_date(phone_number, message)

    if step == "ASK_TIME":
        return handle_time(phone_number, message)

    if step == "CONFIRM_HARVEST":
        return handle_harvest_confirmation(phone_number, message)

    if step == "CONFIRM_CANCEL":
        return handle_cancel_confirmation(phone_number, message)

    return end_session(phone_number, "Something went wrong. Please try again.")


def handle_language(phone_number, choice):
    """
    Saves the farmer's language choice.
    """
    session = SESSIONS[phone_number]

    if choice == "1":
        session["language"] = "en"
    elif choice == "2":
        session["language"] = "rw"
    else:
        return continue_session("Invalid choice.\n" + language_menu())

    session["step"] = "MAIN"
    return continue_session(main_menu(session["farmer"], session["language"]))


def handle_main_menu(phone_number, choice):
    """
    Handles options from the main USSD menu.
    """
    session = SESSIONS[phone_number]
    language = session["language"]

    if choice == "1":
        return start_create_flow(phone_number)

    if choice == "2":
        return show_info_screen(phone_number, pickup_status(phone_number, language))

    if choice == "3":
        return start_update_flow(phone_number)

    if choice == "4":
        return start_cancel_flow(phone_number)

    if choice == "5":
        return show_info_screen(phone_number, sms_messages_screen(phone_number, language))

    if choice == "6":
        return show_info_screen(phone_number, help_menu(language))

    if choice == "7":
        session["step"] = "LANGUAGE"
        return continue_session(language_menu())

    return continue_session(invalid_choice(language) + "\n" + main_menu(session["farmer"], language))


def show_info_screen(phone_number, content):
    """
    Shows read-only screens such as status, SMS inbox, and help.

    The farmer can press 9 to go back to the main menu.
    """
    session = SESSIONS[phone_number]
    language = session["language"]
    session["step"] = "INFO_SCREEN"
    session["info_content"] = content

    if language == "rw":
        return continue_session(content + "\n\n9. Subira inyuma\n0. Sohoka")

    return continue_session(content + "\n\n9. Back\n0. Exit")


def handle_info_screen(phone_number, choice):
    """
    Handles replies from read-only screens.
    """
    session = SESSIONS[phone_number]
    language = session["language"]

    if choice == "9":
        session["step"] = "MAIN"
        return continue_session(main_menu(session["farmer"], language))

    content = session.get("info_content", "")
    return show_info_screen(phone_number, invalid_choice(language) + "\n" + content)


def clear_harvest_draft(session):
    """
    Removes temporary harvest values from the session.

    This prevents old quantity/date/time values from being reused by mistake.
    """
    session.pop("quantity_kg", None)
    session.pop("harvest_date", None)
    session.pop("harvest_time", None)
    session.pop("target_forecast", None)


def start_create_flow(phone_number):
    """
    Starts a new harvest report flow.
    """
    session = SESSIONS[phone_number]
    language = session["language"]

    clear_harvest_draft(session)
    session["action"] = "CREATE"
    session["step"] = "ASK_QUANTITY"

    return continue_session(quantity_prompt(language))


def start_update_flow(phone_number):
    """
    Starts updating the farmer's latest pending harvest report.
    """
    session = SESSIONS[phone_number]
    language = session["language"]
    latest = get_latest_forecast(phone_number)

    if latest is None:
        message = "No harvest report found." if language == "en" else "Nta raporo y'umusaruro yabonetse."
        return show_info_screen(phone_number, message)

    if latest["status"] != "pending":
        message = (
            "Only pending harvest reports can be updated here."
            if language == "en"
            else "Raporo zitarahuzwa nizo zishobora kuvugururwa hano."
        )
        return show_info_screen(phone_number, message)

    clear_harvest_draft(session)
    session["action"] = "UPDATE"
    session["target_forecast"] = latest
    session["step"] = "ASK_QUANTITY"

    if language == "rw":
        intro = (
            "Vugurura raporo iheruka:\n"
            f"Ingano iriho: {latest['quantity_kg']}kg\n"
            f"Itariki: {latest['harvest_date']}\n\n"
        )
    else:
        intro = (
            "Update latest harvest report:\n"
            f"Current quantity: {latest['quantity_kg']}kg\n"
            f"Date: {latest['harvest_date']}\n\n"
        )

    return continue_session(intro + quantity_prompt(language))


def handle_quantity(phone_number, text):
    """
    Validates quantity and moves to date step.

    9 takes the farmer back to the main menu.
    """
    session = SESSIONS[phone_number]
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


def handle_date(phone_number, text):
    """
    Validates date and moves to time step.

    9 returns the farmer to quantity entry.
    """
    session = SESSIONS[phone_number]
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


def handle_time(phone_number, text):
    """
    Validates time and moves to confirmation screen.

    9 returns the farmer to date entry.
    """
    session = SESSIONS[phone_number]
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


def handle_harvest_confirmation(phone_number, choice):
    """
    Saves or updates the harvest report after farmer confirmation.
    """
    session = SESSIONS[phone_number]
    language = session["language"]
    action = session.get("action", "CREATE")

    if choice == "9":
        session["step"] = "ASK_TIME"
        return continue_session(time_prompt(language))

    if choice != "1":
        return continue_session(invalid_choice(language) + "\n" + confirm_harvest_message(session))

    if action == "UPDATE":
        forecast = update_forecast(
            session["target_forecast"],
            session["quantity_kg"],
            session["harvest_date"],
            session["harvest_time"]
        )
        notify_harvest_updated(phone_number, forecast, language)
        return end_session(phone_number, updated_message(language))

    forecast = {
        "phone_number": phone_number,
        "farmer_code": session["farmer"]["farmer_code"],
        "quantity_kg": session["quantity_kg"],
        "harvest_date": session["harvest_date"],
        "harvest_time": session["harvest_time"],
        "status": "pending"
    }

    save_forecast(forecast)
    notify_harvest_recorded(phone_number, forecast, language)

    return end_session(phone_number, submitted_message(language))


def pickup_status(phone_number, language):
    """
    Shows the latest harvest report status.
    """
    latest = get_latest_forecast(phone_number)

    if latest is None:
        return "No harvest report found." if language == "en" else "Nta raporo y'umusaruro yabonetse."

    if language == "rw":
        return (
            "Raporo iheruka:\n"
            f"{latest['quantity_kg']}kg z'inyanya\n"
            f"Itariki: {latest['harvest_date']}\n"
            f"Igihe: {latest['harvest_time']}\n"
            f"Status: {latest['status']}"
        )

    return (
        "Latest harvest report:\n"
        f"{latest['quantity_kg']}kg tomatoes\n"
        f"Date: {latest['harvest_date']}\n"
        f"Time: {latest['harvest_time']}\n"
        f"Status: {latest['status']}"
    )


def sms_messages_screen(phone_number, language):
    """
    Shows the last 3 SMS notifications inside the USSD menu.
    """
    messages = get_recent_notifications(phone_number, limit=3)

    if not messages:
        return "No SMS messages found." if language == "en" else "Nta butumwa bwa SMS buraboneka."

    if language == "rw":
        lines = ["Ubutumwa bwa SMS buheruka:"]
    else:
        lines = ["Latest SMS messages:"]

    for index, notification in enumerate(messages, start=1):
        short_message = notification["message"].replace("\n", " ")

        if len(short_message) > 90:
            short_message = short_message[:90] + "..."

        lines.append(
            f"{index}. {notification['notification_type']} - {short_message}"
        )

    return "\n".join(lines)


def start_cancel_flow(phone_number):
    """
    Starts cancellation for the latest pending harvest report.
    """
    session = SESSIONS[phone_number]
    language = session["language"]
    latest = get_latest_forecast(phone_number)

    if latest is None:
        message = "No harvest report found." if language == "en" else "Nta raporo y'umusaruro yabonetse."
        return show_info_screen(phone_number, message)

    if latest["status"] != "pending":
        message = (
            "This harvest report cannot be cancelled here. Please contact the admin."
            if language == "en"
            else "Iyi raporo ntishobora gusibwa hano. Vugana na admin."
        )
        return show_info_screen(phone_number, message)

    session["step"] = "CONFIRM_CANCEL"
    session["cancel_forecast"] = latest

    if language == "rw":
        return continue_session(
            "Siba raporo iheruka?\n"
            f"Ingano: {latest['quantity_kg']}kg z'inyanya\n"
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


def handle_cancel_confirmation(phone_number, choice):
    """
    Cancels the latest pending harvest report.
    """
    session = SESSIONS[phone_number]
    language = session["language"]

    if choice == "9":
        session["step"] = "MAIN"
        return continue_session(main_menu(session["farmer"], language))

    if choice != "1":
        return continue_session(invalid_choice(language))

    forecast = cancel_forecast(session["cancel_forecast"])
    notify_harvest_cancelled(phone_number, forecast, language)

    return end_session(phone_number, cancelled_message(language))