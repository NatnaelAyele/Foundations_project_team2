from ussd_gateway.ussd_app import handle_ussd
from ussd_gateway.farmers import normalize_phone
from sms_gateway.notifier import get_sent_notifications, clear_notifications
from ussd_gateway.session_store import reset_state


def print_ussd_screen(response):
    """
    Prints USSD response like a phone screen.
    """
    clean_response = response.replace("CON ", "").replace("END ", "")

    print("\n========== USSD SCREEN ==========")
    print(clean_response)
    print("=================================\n")


def print_sms_inbox(phone_number):
    """
    Shows all SMS messages when the tester types INBOX.
    """
    messages = get_sent_notifications(phone_number)

    print("\n========== SMS INBOX ==========")

    if not messages:
        print("No SMS messages received yet.")
    else:
        for message in messages:
            print("From: Tomato Logistics")
            print(f"Time: {message['sent_at']}")
            print(f"Type: {message['notification_type']}")
            print(message["message"])
            print("------------------------------")

    print("===============================\n")


def run_ussd_session(phone_number):
    """
    Runs one simulated USSD session.
    """
    phone_number = normalize_phone(phone_number)

    print("\nDialing *304#...")

    response = handle_ussd(phone_number, "")
    print_ussd_screen(response)

    while not response.startswith("END"):
        reply = input("USSD Reply: ").strip()

        if reply.upper() == "EXIT":
            print("USSD session stopped.")
            return

        if reply.upper() == "INBOX":
            print_sms_inbox(phone_number)
            continue

        response = handle_ussd(phone_number, reply)
        print_ussd_screen(response)

    print("USSD session closed.\n")


def run_live_demo():
    """
    Runs the phone simulator.

    Type INBOX anytime to view all received SMS messages.
    """
    reset_state()
    clear_notifications()

    print("\nTomato Logistics Phone Simulator")
    print("-----------------------------------------")
    print("Enter your registered number to continue.")
    print("Eg: +250788000001 or 0788000001")
    print("Type EXIT to stop the simulator.\n")

    while True:
        phone_number = input("Farmer phone number: ").strip()

        if phone_number.upper() == "EXIT":
            print("Phone simulator stopped.")
            break

        run_ussd_session(phone_number)

        again = input("Start another session? yes/no: ").strip().lower()

        if again not in ["yes", "y"]:
            print("Phone simulator stopped.")
            break


if __name__ == "__main__":
    run_live_demo()