import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ussd_gateway import menus
from ussd_gateway.ussd_app import continue_session, end_session


def test_language_menu_contains_both_supported_languages():
    menu = menus.language_menu()

    assert "1. English" in menu
    assert "2. Kinyarwanda" in menu


def test_main_menu_changes_with_the_selected_language():
    farmer = {"farmer_code": "FRM-001"}

    english = menus.main_menu(farmer, "en")
    kinyarwanda = menus.main_menu(farmer, "rw")

    assert "Report tomato harvest" in english
    assert "Andika umusaruro" in kinyarwanda


def test_ussd_continuing_and_ending_messages_use_required_prefixes():
    assert continue_session("Choose an option") == "CON Choose an option"
    assert end_session("missing-session", "Goodbye") == "END Goodbye"


def test_harvest_confirmation_uses_the_selected_language_and_action():
    session = {
        "language": "en",
        "action": "CREATE",
        "quantity_kg": 300,
        "harvest_date": "2026-07-29",
        "harvest_time": "08:00",
    }

    message = menus.confirm_harvest_message(session)

    assert "Confirm your harvest report" in message
    assert "300kg" in message
    assert "1. Submit" in message


def test_invalid_choice_returns_a_safe_message():
    assert "Invalid choice" in menus.invalid_choice("en")
    assert menus.invalid_choice("rw")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
