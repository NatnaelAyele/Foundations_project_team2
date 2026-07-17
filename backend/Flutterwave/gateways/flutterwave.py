import base64
import hashlib
import hmac
import uuid

import httpx

from backend.Flutterwave.payment_gateway import PaymentGateway
from backend.config import Config


class FlutterwaveGatewayError(RuntimeError):
    pass


class FlutterwaveConfigurationError(FlutterwaveGatewayError):
    pass


class FlutterwaveGateway(PaymentGateway):
    """HTTP adapter for Flutterwave Standard Checkout."""

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        webhook_secret: str | None = None,
        base_url: str | None = None,
        api_base_url: str | None = None,
        app_base_url: str | None = None,
        timeout_seconds: float = 20.0,
    ):
        self.public_key = public_key or Config.FLUTTERWAVE_PUBLIC_KEY
        self.secret_key = secret_key or Config.FLUTTERWAVE_SECRET_KEY
        self.webhook_secret = webhook_secret or Config.FLUTTERWAVE_WEBHOOK_SECRET
        self.base_url = (base_url or Config.FLUTTERWAVE_BASE_URL).rstrip("/")
        self.api_base_url = (api_base_url or app_base_url or Config.API_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def initialize_payment(self, payment):
        payload = {
            "tx_ref": payment["tx_ref"],
            "amount": float(payment["amount"]),
            "currency": payment["currency"],
            "redirect_url": self.callback_url(),
            "customer": {
                "email": payment.get("customer_email") or self.default_email(payment),
                "name": payment.get("customer_name") or "FreshLink Farmer",
                "phonenumber": payment.get("payer_phone"),
            },
            "customizations": {
                "title": "FreshLink Tomato Logistics",
                "description": payment.get("purpose", "Trip transport and storage"),
            },
            "meta": {
                "allocation_id": payment.get("allocation_id"),
                "farmer_id": payment.get("farmer_id"),
                "payment_reference": payment.get("payment_reference"),
            },
        }
        response = self.post("/payments", payload, idempotency_key=payment["tx_ref"])
        link = response.get("data", {}).get("link")
        if response.get("status") != "success" or not link:
            raise FlutterwaveGatewayError(response.get("message") or "Payment initialization failed")
        return {
            "status": "success",
            "payment_status": "INITIALIZED",
            "provider_status": response.get("status"),
            "payment_link": link,
            "tx_ref": payment["tx_ref"],
            "raw_response": response,
        }

    def verify_payment(self, tx_ref, transaction_id=None):
        if transaction_id:
            response = self.get(f"/transactions/{transaction_id}/verify")
        else:
            response = self.get(
                "/transactions/verify_by_reference",
                params={"tx_ref": tx_ref},
            )
        data = response.get("data") or {}
        return {
            "status": response.get("status"),
            "message": response.get("message"),
            "payment_status": self.map_transaction_status(data.get("status")),
            "provider_status": data.get("status"),
            "tx_ref": data.get("tx_ref") or tx_ref,
            "transaction_id": data.get("id"),
            "flutterwave_ref": data.get("flw_ref"),
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "raw_response": response,
        }

    def refund_payment(self, tx_ref, transaction_id=None, amount=None, reason=None):
        if not transaction_id:
            verified = self.verify_payment(tx_ref)
            transaction_id = verified.get("transaction_id")
        if not transaction_id:
            raise FlutterwaveGatewayError("A Flutterwave transaction ID is required for refunds")
        payload = {}
        if amount is not None:
            payload["amount"] = float(amount)
        if reason:
            payload["comments"] = reason
        response = self.post(
            f"/transactions/{transaction_id}/refund",
            payload,
            idempotency_key=f"refund-{tx_ref}",
        )
        data = response.get("data") or {}
        return {
            "status": response.get("status"),
            "message": response.get("message"),
            "payment_status": "REFUNDED" if response.get("status") == "success" else "FAILED",
            "provider_status": data.get("status"),
            "tx_ref": tx_ref,
            "transaction_id": transaction_id,
            "raw_response": response,
        }

    def verify_webhook_signature(self, raw_body, signature):
        if not self.webhook_secret or not signature:
            return False
        body = raw_body if isinstance(raw_body, bytes) else str(raw_body).encode("utf-8")
        digest = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    def callback_url(self):
        return f"{self.api_base_url}/api/payments/flutterwave/callback"

    def default_email(self, payment):
        farmer_id = payment.get("farmer_id") or "unknown"
        return f"farmer-{farmer_id}@freshlink.local"

    def headers(self, idempotency_key=None):
        if not self.secret_key:
            raise FlutterwaveConfigurationError("FLUTTERWAVE_SECRET_KEY is not configured")
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["X-Idempotency-Key"] = str(idempotency_key)
            headers["X-Trace-Id"] = str(uuid.uuid4())
        return headers

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def post(self, path, payload, idempotency_key=None):
        return self.request(
            "POST",
            path,
            json=payload,
            idempotency_key=idempotency_key,
        )

    def request(self, method, path, **kwargs):
        idempotency_key = kwargs.pop("idempotency_key", None)
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=self.headers(idempotency_key),
                    **kwargs,
                )
                data = response.json()
        except httpx.TimeoutException as error:
            raise FlutterwaveGatewayError("Flutterwave request timed out") from error
        except httpx.HTTPError as error:
            raise FlutterwaveGatewayError("Flutterwave is unavailable") from error
        except ValueError as error:
            raise FlutterwaveGatewayError("Flutterwave returned an invalid response") from error

        if response.status_code >= 400:
            message = data.get("message") if isinstance(data, dict) else None
            raise FlutterwaveGatewayError(message or "Flutterwave request failed")
        return data

    def map_transaction_status(self, provider_status):
        normalized = str(provider_status or "").lower()
        if normalized == "successful":
            return "PAID"
        if normalized in {"failed", "error"}:
            return "FAILED"
        if normalized in {"cancelled", "canceled"}:
            return "CANCELLED"
        return "PENDING"
