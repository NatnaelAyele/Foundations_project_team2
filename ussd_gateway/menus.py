from datetime import date, timedelta


def language_menu():
    """
    First screen where the farmer chooses language.
    """
    return (
        "Welcome to Tomato Logistics\n"
        "1. English\n"
        "2. Kinyarwanda"
    )


def main_menu(farmer, language):
    """
    Main farmer menu.
    """
    if language == "rw":
        return (
            f"Murakaza neza {farmer['farmer_code']}\n"
            "1. Andika umusaruro w'inyanya\n"
            "2. Reba aho gahunda yo gufata igeze\n"
            "3. Ibyo wishyura\n"
            "4. Vugurura raporo iheruka\n"
            "5. Siba raporo iheruka\n"
            "6. Reba ubutumwa bwa SMS\n"
            "7. Ubufasha\n"
            "8. Hindura ururimi\n"
            "0. Sohoka"
        )

    return (
        f"Welcome {farmer['farmer_code']}\n"
        "1. Report tomato harvest\n"
        "2. Check pickup status\n"
        "3. Payments\n"
        "4. Update latest harvest report\n"
        "5. Cancel latest harvest report\n"
        "6. View my SMS messages\n"
        "7. Help\n"
        "8. Change language\n"
        "0. Exit"
    )


def payments_menu(language):
    """Shows the payment submenu for farmers."""
    if language == "rw":
        return (
            "Ibyo wishyura:\n"
            "1. Ibyo wishyura bitarangiye\n"
            "2. Amateka yo kwishyura\n"
            "3. Status yo kwishyura\n"
            "4. Subira inyuma"
        )

    return (
        "Payments:\n"
        "1. Pending payments\n"
        "2. Payment history\n"
        "3. Payment status\n"
        "4. Back"
    )


def quantity_prompt(language):
    """
    Asks farmer to enter tomato quantity.
    """
    if language == "rw":
        return "Andika ingano y'inyanya muri kg.(nka: 300)\n9. Subira inyuma\n0. Sohoka"

    return "Enter tomato quantity in kg. (e.g: 300)\n9. Back\n0. Exit"


def date_prompt(language):
    """
    Asks farmer to enter harvest date.

    The example date is generated as tomorrow so the prompt never
    teaches farmers to type a date that is already in the past.
    """
    example = (date.today() + timedelta(days=1)).isoformat()

    if language == "rw":
        return f"Andika itariki yo gusarura.(nka: {example})\n9. Subira inyuma\n0. Sohoka"

    return f"Enter harvest date. (e.g: {example})\n9. Back\n0. Exit"


def time_prompt(language):
    """
    Asks farmer to enter harvest time.
    """
    if language == "rw":
        return "Andika isaha yo gusarura.(nka): 08:00)\n9. Subira inyuma\n0. Sohoka"

    return "Enter harvest time.(e.g: 08:00)\n9. Back\n0. Exit"


def confirm_harvest_message(session):
    """
    Final confirmation screen for report or update.
    """
    language = session["language"]
    action = session.get("action", "CREATE")

    if language == "rw":
        title = "Emeza raporo y'umusaruro:" if action == "CREATE" else "Emeza kuvugurura raporo:"
        submit_word = "Ohereza" if action == "CREATE" else "Vugurura"

        return (
            f"-----------------------------------\n{title}\n"
            f"Ingano: {session['quantity_kg']}kg z'inyanya\n"
            f"Itariki: {session['harvest_date']}\n"
            f"Igihe: {session['harvest_time']}\n\n"
            f"1. {submit_word}\n"
            "9. Subira inyuma\n"
            "0. Sohoka"
        )

    title = "Confirm your harvest report:" if action == "CREATE" else "Confirm harvest update:"
    submit_word = "Submit" if action == "CREATE" else "Update"

    return (
        f"------------------------------------\n{title}\n"
        f"Quantity: {session['quantity_kg']}kg tomatoes\n"
        f"Date: {session['harvest_date']}\n"
        f"Time: {session['harvest_time']}\n\n"
        f"1. {submit_word}\n"
        "9. Back\n"
        "0. Exit"
    )


def submitted_message(language):
    """
    Final USSD screen after a harvest report is submitted.

    Tells the farmer clearly that the work is done and an SMS is coming,
    so even if Africa's Talking shows a timeout afterwards, the farmer
    already knows the submission succeeded.
    """
    if language == "rw":
        return (
            "BYAKUNZE\n"
            "Raporo y'umusaruro yoherejwe neza.\n\n"
            "Tegereza ubutumwa bwa SMS bwo kwemeza.\n\n"
        )

    return (
        "SUBMITTED\n"
        "Your harvest report has been submitted.\n\n"
        "Please wait for an SMS confirmation.\n\n"
    )


def updated_message(language):
    """
    Final USSD screen after a harvest report is updated.
    """
    if language == "rw":
        return (
            "BYAVUGURUWE\n"
            "Raporo y'umusaruro yavuguruwe neza.\n\n"
            "Tegereza ubutumwa bwa SMS bwo kwemeza.\n\n"
        )

    return (
        "UPDATED\n"
        "Your harvest report has been updated.\n\n"
        "Please wait for an SMS confirmation.\n\n"
    )


def cancelled_message(language):
    """
    Final USSD screen after a harvest report is cancelled.
    """
    if language == "rw":
        return (
            "BYASIBWE\n"
            "Raporo y'umusaruro yasibwe neza.\n\n"
            "Tegereza ubutumwa bwa SMS bwo kwemeza.\n\n"
        )

    return (
        "CANCELLED\n"
        "Your harvest report has been cancelled.\n\n"
        "Please wait for an SMS confirmation.\n\n"
    )


def help_menu(language):
    """
    Shows simple usage instructions.
    """
    if language == "rw":
        return (
            "Ubufasha:\n"
            "1 = Andika umusaruro\n"
            "2 = Reba status\n"
            "3 = Vugurura raporo\n"
            "4 = Siba raporo\n"
            "5 = Reba SMS\n"
            "9 = Subira inyuma\n"
            "0 = Sohoka"
        )

    return (
        "Help:\n"
        "1 = Report harvest\n"
        "2 = Check status\n"
        "3 = Payments\n"
        "4 = Update latest report\n"
        "5 = Cancel latest report\n"
        "6 = View SMS\n"
        "9 = Back\n"
        "0 = Exit"
    )


def invalid_choice(language):
    """
    Message for wrong menu choice.
    """
    if language == "rw":
        return "Wahisemo nabi. Ongera ugerageze."

    return "Invalid choice. Please try again."


def invalid_quantity(language):
    """
    Message for invalid quantity.
    """
    if language == "rw":
        return "Ingano siyo. \nAndika umubare gusa.(nka: 300)"

    return "Invalid quantity. \nEnter a number only.(e.g: 300)"


def invalid_date(language):
    """
    Message for invalid date format.
    """
    example = (date.today() + timedelta(days=1)).isoformat()

    if language == "rw":
        return f"Itariki siyo.\nKoresha YYYY-MM-DD. (nka: {example})"

    return f"Invalid date format.\nUse YYYY-MM-DD. (e.g: {example})"


def invalid_time(language):
    """
    Message for invalid time format.
    """
    if language == "rw":
        return "Igihe si cyo.\nKoresha HH:MM. (nka: 08:00)"

    return "Invalid time format.\nUse HH:MM. (e.g: 08:00)"

def invalid_date_range(language, window_days_ahead):
    """
    Message when the date format is right but the date is in the past
    or beyond the coordination window, so the engine would silently
    exclude it. Telling the farmer NOW lets them correct it while the
    session is still open.
    """
    today = date.today()
    last_day = today + timedelta(days=window_days_ahead)

    if language == "rw":
        return (
            "Itariki igomba kuba hagati ya\n"
            f"{today.isoformat()} na {last_day.isoformat()}."
        )

    return (
        "Date must be between\n"
        f"{today.isoformat()} and {last_day.isoformat()}."
    )


def quantity_too_large(language, max_quantity_kg):
    """
    Message when the quantity is above the sanity ceiling. Catches
    typos like 40000 instead of 400 before they become forecasts no
    truck can ever carry.
    """
    if language == "rw":
        return (
            f"Ingano irenze {max_quantity_kg:,.0f}kg.\n"
            "Genzura umubare wanditse cyangwa\n"
            "uvugane n'ubuyobozi ku misaruro minini."
        )

    return (
        f"Quantity is above {max_quantity_kg:,.0f}kg.\n"
        "Please check your entry, or contact\n"
        "the admin for very large harvests."
    )