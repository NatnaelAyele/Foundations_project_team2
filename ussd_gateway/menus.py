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
            "3. Vugurura raporo iheruka\n"
            "4. Siba raporo iheruka\n"
            "5. Reba ubutumwa bwa SMS\n"
            "6. Ubufasha\n"
            "7. Hindura ururimi\n"
            "0. Sohoka"
        )

    return (
        f"Welcome {farmer['farmer_code']}\n"
        "1. Report tomato harvest\n"
        "2. Check pickup status\n"
        "3. Update latest harvest report\n"
        "4. Cancel latest harvest report\n"
        "5. View my SMS messages\n"
        "6. Help\n"
        "7. Change language\n"
        "0. Exit"
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
    """
    if language == "rw":
        return "Andika itariki yo gusarura.(nka: 2026-07-03)\n9. Subira inyuma\n0. Sohoka"

    return "Enter harvest date. (e.g: 2026-07-03)\n9. Back\n0. Exit"


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
    USSD message after successful harvest submission.
    """
    if language == "rw":
        return "Raporo y'umusaruro yoherejwe neza.\nUrahita ubona ubutumwa bwa SMS."

    return "Harvest report submitted successfully.\nYou will receive an SMS confirmation."


def updated_message(language):
    """
    USSD message after successful harvest update.
    """
    if language == "rw":
        return "Raporo y'umusaruro yavuguruwe neza.\nUrahita ubona ubutumwa bwa SMS."

    return "Harvest report updated successfully.\nYou will receive an SMS confirmation."


def cancelled_message(language):
    """
    USSD message after successful harvest cancellation.
    """
    if language == "rw":
        return "Raporo y'umusaruro yasibwe neza.\nUrahita ubona ubutumwa bwa SMS."

    return "Harvest report cancelled successfully.\nYou will receive an SMS confirmation."


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
        "3 = Update latest report\n"
        "4 = Cancel latest report\n"
        "5 = View SMS\n"
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
    if language == "rw":
        return "Itariki siyo.\nKoresha YYYY-MM-DD. (nka: 2026-07-03)"

    return "Invalid date format.\nUse YYYY-MM-DD. (e.g: 2026-07-03)"


def invalid_time(language):
    """
    Message for invalid time format.
    """
    if language == "rw":
        return "Igihe si cyo.\nKoresha HH:MM. (nka: 08:00)"

    return "Invalid time format.\nUse HH:MM. (e.g: 08:00)"