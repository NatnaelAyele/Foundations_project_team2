from ussd_gateway.ussd_app import handle_ussd


def print_response(response):
    """
    Prints the USSD response in a clean format for terminal testing.

    CON means the session continues.
    END means the session closes.
    """
    print("\n----- USSD SCREEN -----")
    print(response.replace("CON ", "").replace("END ", ""))
    print("-----------------------\n")


def run_demo():
    """
    Runs a terminal-based USSD simulation.

    This lets the team test the farmer experience without paying for
    a real USSD code like *304#.
    """
    print("\nTomato Logistics USSD Demo")
    print("--------------------------")
    print("This simulates dialing *304#.")
    print("Use a registered phone number:")
    print("+250788000001 or 0788000001")
    print("Type EXIT to stop.\n")

    phone_number = input("Farmer phone number: ")

    print("\nDialing *304#...\n")

    # Empty message means the farmer has just opened the USSD service.
    response = handle_ussd(phone_number, "")
    print_response(response)

    while True:
        message = input("Reply: ")

        if message.upper() == "EXIT":
            print("Demo stopped.")
            break

        response = handle_ussd(phone_number, message)
        print_response(response)

        # In real USSD, the session closes when the response begins with END.
        if response.startswith("END"):
            break


if __name__ == "__main__":
    run_demo()