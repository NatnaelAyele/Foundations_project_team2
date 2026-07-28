import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sms_gateway import notifier
from ussd_gateway.farmers import normalize_phone, phone_lookup_candidates


@pytest.mark.parametrize(
    ("raw_phone", "expected"),
    [
        ("0788000001", "+250788000001"),
        ("250788000001", "+250788000001"),
        ("+250 788-000-001", "+250788000001"),
    ],
)
def test_farmer_phone_numbers_are_normalized(raw_phone, expected):
    assert normalize_phone(raw_phone) == expected


def test_phone_lookup_includes_international_and_local_rwanda_formats():
    assert phone_lookup_candidates("0788000001") == [
        "+250788000001",
        "0788000001",
    ]


@pytest.mark.parametrize(
    ("raw_phone", "expected"),
    [
        ("0788000001", "+250788000001"),
        ("250788000001", "+250788000001"),
        ("+250788000001", "+250788000001"),
    ],
)
def test_sms_phone_numbers_use_e164_format(raw_phone, expected):
    assert notifier.normalize_sms_phone(raw_phone) == expected


def test_sms_base_url_requires_https(monkeypatch):
    monkeypatch.setenv("AT_SMS_BASE_URL", "http://sandbox.example.test:443/messages")

    with pytest.raises(RuntimeError, match="cannot use plain HTTP"):
        notifier.get_sms_base_url()


def test_sms_send_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("AT_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="API key is not configured"):
        notifier.send_sms_over_https("0788000001", "Test message")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
