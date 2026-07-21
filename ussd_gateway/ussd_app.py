import concurrent.futures
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.services.payment_service import PaymentService, PaymentServiceError, PaymentStatus
from sms_gateway.notifier import get_recent_notifications
from ussd_gateway.farmers import get_farmer_by_phone, normalize_phone
from ussd_gateway.forecast_repository import (
    save_forecast,
    get_latest_forecast,
    get_latest_pending_forecast,
    update_forecast,
    cancel_forecast
)
from backend.services.coordination_service import (
    CoordinationService,
    CoordinationPersistenceError,
)
from backend.models.provider import Farmer
from ussd_gateway.menus import (
    language_menu,
    main_menu,
    payments_menu,
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
    invalid_time,
    invalid_date_range,
    quantity_too_large
)
from ussd_gateway.notifications import (
    notify_harvest_recorded,
    notify_harvest_updated,
    notify_harvest_cancelled
)
from ussd_gateway.session_store import SESSIONS, touch, sweep_expired
from backend.services.harvest_service import HarvestService

MAX_QUANTITY_KG = 10000

COORDINATION_WINDOW_DAYS_AHEAD = 3

_coordination_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def run_coordination_in_background(farmer_id):
    """
    Runs the coordination engine for the farmer's sector in a background
    thread with its OWN database session (SQLAlchemy sessions are not
    thread-safe, so the request's session is never shared across threads).

    Failures are logged and swallowed: the farmer's forecast is already
    saved, and the scheduler will retry coordination on its next cycle.
    """
    db = SessionLocal()
    try:
        farmer = db.get(Farmer, farmer_id)
        if farmer is None:
            return
        CoordinationService(db).run_sector(farmer.sector_id)
    except CoordinationPersistenceError as error:
        print(f"[background coordination] skipped: {error}")
    except Exception as error:
        print(f"[background coordination] failed: {error}")
    finally:
        db.close()


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
    Main USSD controller used by both the terminal and the FastAPI
    FastAPI passes session_id from Africa's Talking.
    """
    phone_number = normalize_phone(phone_number)
    message = message.strip()
    session_key = session_id or phone_number

    sweep_expired()

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
        touch(session_key)
        return continue_session(language_menu())

    session = SESSIONS[session_key]
    touch(session_key)

    if message == "0":
        return end_session(session_key, exit_message(session["language"]))

    step = session["step"]

    if step == "LANGUAGE":
        return handle_language(session_key, message)

    if step == "MAIN":
        return handle_main_menu(session_key, message)

    if step == "PAYMENTS_MENU":
        return handle_payments_menu(session_key, message)

    if step == "PAYMENT_ACTION":
        return handle_payment_action(session_key, message)

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
        return start_payments_flow(session_key)

    if choice == "4":
        return start_update_flow(session_key)

    if choice == "5":
        return start_cancel_flow(session_key)

    if choice == "6":
        return show_info_screen(session_key, sms_messages_screen(session["farmer"], language))

    if choice == "7":
        return show_info_screen(session_key, help_menu(language))

    if choice == "8":
        session["step"] = "LANGUAGE"
        return continue_session(language_menu())

    return continue_session(invalid_choice(language) + "\n" + main_menu(session["farmer"], language))


def show_info_screen(session_key, content, return_step="MAIN"):
    """
    Shows read-only screens such as status, SMS inbox, and help.
    """
    session = SESSIONS[session_key]
    language = session["language"]
    session["step"] = "INFO_SCREEN"
    session["return_step"] = return_step

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
        return_step = session.get("return_step", "MAIN")
        if return_step == "PAYMENTS_MENU":
            session["step"] = "PAYMENTS_MENU"
            return continue_session(payments_menu(language))
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


def start_payments_flow(session_key):
    """Starts the payment submenu for the farmer."""
    session = SESSIONS[session_key]
    session["step"] = "PAYMENTS_MENU"
    return continue_session(payments_menu(session["language"]))


def handle_payments_menu(session_key, choice):
    """Routes payment submenu options to the appropriate USSD screens."""
    session = SESSIONS[session_key]
    language = session["language"]
    farmer = session["farmer"]

    if choice == "1":
        return show_pending_payments(session_key)

    if choice == "2":
        return show_info_screen(session_key, payment_history_screen(farmer, language), return_step="PAYMENTS_MENU")

    if choice == "3":
        return show_info_screen(session_key, payment_status_screen(farmer, language), return_step="PAYMENTS_MENU")

    if choice == "4":
        session["step"] = "MAIN"
        return continue_session(main_menu(session["farmer"], language))

    return continue_session(invalid_choice(language) + "\n\n" + payments_menu(language))


def show_pending_payments(session_key):
    """Shows the first pending payment and allows the farmer to pay it."""
    session = SESSIONS[session_key]
    farmer = session["farmer"]
    language = session["language"]

    payment = get_pending_payment(farmer)
    if payment is None:
        return show_info_screen(
            session_key,
            "No pending payments found." if language == "en" else "Nta byo wishyura bitegereje byabonetse.",
            return_step="PAYMENTS_MENU",
        )

    session["payment_selection"] = payment
    session["step"] = "PAYMENT_ACTION"

    content = (
        f"Trip\n{payment['trip_label']}\n\n"
        f"Amount\n{format_amount(payment['amount'])}\n\n"
        f"Status\n{format_status(payment['payment_status'], language)}\n\n"
        "1. Pay\n"
        "2. Back"
    )
    return continue_session(content)


def handle_payment_action(session_key, choice):
    """Initializes payment through PaymentService when the farmer confirms."""
    session = SESSIONS[session_key]
    language = session["language"]
    farmer = session["farmer"]

    if choice == "2":
        session["step"] = "PAYMENTS_MENU"
        return continue_session(payments_menu(language))

    if choice != "1":
        return continue_session(invalid_choice(language) + "\n\n1. Pay\n2. Back")

    payment = session.get("payment_selection")
    if payment is None:
        session["step"] = "PAYMENTS_MENU"
        return continue_session(payments_menu(language))

    try:
        db = SessionLocal()
        service = PaymentService(db)
        result = service.initialize_momo_payment(payment["allocation_id"], farmer["farmer_id"])
        db.close()
    except PaymentServiceError:
        return end_session(session_key, "Payment could not be initialized right now. Please try again later.")

    session["step"] = "PAYMENTS_MENU"
    message = (
        "Payment started. Approve the Mobile Money request on your phone "
        "with your PIN to complete payment."
        if language == "en"
        else "Kwishyura byatangiye. Emeza ubutumwa bwa Mobile Money kuri "
             "telefoni yawe wandika PIN kugirango urangize kwishyura."
    )
    return end_session(session_key, message)


def get_pending_payment(farmer):
    """Returns the first payment that is not completed for the farmer."""
    try:
        db = SessionLocal()
        service = PaymentService(db)
        payments = service.get_farmer_payment_overview(farmer["farmer_id"])
        db.close()
    except PaymentServiceError:
        return None

    for payment in payments:
        if payment.get("payment_status") not in {PaymentStatus.PAID, PaymentStatus.REFUNDED}:
            return payment
    return None


def payment_history_screen(farmer, language):
    """Shows recent payment history for the farmer."""
    try:
        db = SessionLocal()
        service = PaymentService(db)
        payments = service.get_farmer_payment_overview(farmer["farmer_id"])
        db.close()
    except PaymentServiceError:
        payments = []

    if not payments:
        return "No payment history found." if language == "en" else "Nta mateka yo kwishyura yabonetse."

    lines = ["Recent payments:"] if language == "en" else ["Amateka yo kwishyura:"]
    for index, payment in enumerate(payments[:3], start=1):
        lines.append(
            f"{index}. {payment['trip_label']} - {format_amount(payment['amount'])} - {format_status(payment['payment_status'], language)}"
        )
    return "\n".join(lines)


def payment_status_screen(farmer, language):
    """Shows the latest payment status for the farmer."""
    try:
        db = SessionLocal()
        service = PaymentService(db)
        payments = service.get_farmer_payment_overview(farmer["farmer_id"])
        db.close()
    except PaymentServiceError:
        payments = []

    if not payments:
        return "No payment found." if language == "en" else "Nta kwishyura byabonetse."

    latest = payments[0]
    return (
        f"Latest payment\n{latest['trip_label']}\n\n"
        f"Amount\n{format_amount(latest['amount'])}\n\n"
        f"Status\n{format_status(latest['payment_status'], language)}"
    )


def format_status(status, language):
    if language == "rw":
        return {
            PaymentStatus.CREATED: "Yatangiye",
            PaymentStatus.INITIALIZED: "Yatangiye",
            PaymentStatus.PENDING: "Bitegereje",
            PaymentStatus.PAID: "Byishyuwe",
            PaymentStatus.FAILED: "Byanze",
            PaymentStatus.CANCELLED: "Byahagaritswe",
            PaymentStatus.REFUNDED: "Byagaruwe",
        }.get(status, status)

    return {
        PaymentStatus.CREATED: "Created",
        PaymentStatus.INITIALIZED: "Initialized",
        PaymentStatus.PENDING: "Pending",
        PaymentStatus.PAID: "Paid",
        PaymentStatus.FAILED: "Failed",
        PaymentStatus.CANCELLED: "Cancelled",
        PaymentStatus.REFUNDED: "Refunded",
    }.get(status, status)


def format_amount(amount):
    return f"{amount:,.0f} RWF"


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

    if quantity_kg > MAX_QUANTITY_KG:
        return continue_session(
            quantity_too_large(language, MAX_QUANTITY_KG)
            + "\n\n" + quantity_prompt(language)
        )

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
        entered_date = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return continue_session(invalid_date(language))

    today = date.today()
    last_allowed = today + timedelta(days=COORDINATION_WINDOW_DAYS_AHEAD)
    if entered_date < today or entered_date > last_allowed:
        return continue_session(
            invalid_date_range(language, COORDINATION_WINDOW_DAYS_AHEAD)
            + "\n\n" + date_prompt(language)
        )

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

    db = SessionLocal()
    service = HarvestService(db)

    try:
        if action == "UPDATE":
            target = session["target_forecast"]

            forecast_obj = service.update_harvest(
                target["forecast_id"],
                session["quantity_kg"],
                session["harvest_date"],
                session["harvest_time"],
                trigger_coordination=False
            )

            # Convert ORM object to dict for the notifier
            forecast = {
                "forecast_id": forecast_obj.forecast_id,
                "quantity_kg": forecast_obj.quantity_kg,
                "harvest_date": forecast_obj.harvest_date,
                "harvest_time": forecast_obj.harvest_time,
                "status": forecast_obj.status
            }

            notify_harvest_updated(farmer, forecast, language)

            _coordination_executor.submit(
                run_coordination_in_background, farmer["farmer_id"]
            )
            return end_session(session_key, updated_message(language))

        forecast_obj = service.create_harvest(
            farmer["farmer_id"],
            session["quantity_kg"],
            session["harvest_date"],
            session["harvest_time"],
            trigger_coordination=False
        )

        forecast = {
            "forecast_id": forecast_obj.forecast_id,
            "quantity_kg": forecast_obj.quantity_kg,
            "harvest_date": forecast_obj.harvest_date,
            "harvest_time": forecast_obj.harvest_time,
            "status": forecast_obj.status
        }

        notify_harvest_recorded(farmer, forecast, language)


        _coordination_executor.submit(
            run_coordination_in_background, farmer["farmer_id"]
        )
        return end_session(session_key, submitted_message(language))
    finally:
        db.close()


def format_report_date(value):
    """
    Shows dates as YYYY-MM-DD instead of "2026-07-03 00:00:00".
    Handles datetime, date, and string values from the database.
    """
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


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
            f"Itariki: {format_report_date(latest['harvest_date'])}\n"
            f"Igihe: {str(latest['harvest_time'])[:5]}\n"
            f"Status: {latest['status']}"
        )

    return (
        "Latest harvest report:\n"
        f"Quantity: {latest['quantity_kg']}kg tomatoes\n"
        f"Date: {format_report_date(latest['harvest_date'])}\n"
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