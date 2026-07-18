# Farmer SMS inbox viewer.

from backend.database import fetch_one, fetch_all
from ussd_gateway.farmers import normalize_phone


def get_farmer_by_phone_any_status(phone_number):
    """
    Finds a farmer by phone number for inbox lookup.
    """
    phone_number = normalize_phone(phone_number)

    return fetch_one(
        """
        SELECT farmer_id, farmer_code, name, phone
        FROM farmers
        WHERE phone = %s
        """,
        (phone_number,)
    )


def get_inbox(farmer_id, limit=None):
    """
    Reads the farmer's notifications, newest first.
    """
    if limit:
        return fetch_all(
            """
            SELECT notification_id, notification_type, message,
                   language, status, sent_time
            FROM notifications
            WHERE farmer_id = %s
            ORDER BY sent_time DESC
            LIMIT %s
            """,
            (farmer_id, limit)
        )

    return fetch_all(
        """
        SELECT notification_id, notification_type, message,
               language, status, sent_time
        FROM notifications
        WHERE farmer_id = %s
        ORDER BY sent_time DESC
        """,
        (farmer_id,)
    )


def print_message(index, notification, highlight=False):
    """
    Prints one SMS the way a phone inbox would show it.
    """
    marker = "  LATEST" if highlight else ""

    print(f"\n[{index}] {notification['notification_type']}{marker}")
    print(f"    Sent:   {notification['sent_time']}")
    print(f"    Status: {notification['status']}")
    print("    " + "-" * 46)

    for line in notification["message"].split("\n"):
        print(f"    {line}")


def run_inbox():
    """
    Asks for a phone number and prints that farmer's SMS inbox.
    """
    print("\nFreshLink SMS Inbox (simulation)")
    print("--------------------------------")
    print("Reads the notifications table directly.")
    print("Type EXIT to stop.\n")

    while True:
        phone_number = input("Farmer phone number: ").strip()

        if not phone_number or phone_number.upper() == "EXIT":
            print("Closed.\n")
            return

        farmer = get_farmer_by_phone_any_status(phone_number)

        if farmer is None:
            print(f"\nNo farmer registered with {normalize_phone(phone_number)}.\n")
            continue

        messages = get_inbox(farmer["farmer_id"])

        print("\n" + "=" * 54)
        print(f" INBOX — {farmer['name']} ({farmer['farmer_code']})")
        print(f" {farmer['phone']}")
        print("=" * 54)

        if not messages:
            print("\n  No messages yet.\n")
        else:
            print(f"\n  {len(messages)} message(s), newest first:")
            for index, notification in enumerate(messages, start=1):
                print_message(index, notification, highlight=(index == 1))

        print("\n" + "=" * 54 + "\n")


if __name__ == "__main__":
    run_inbox()