"""
Mock Flutterwave gateway for the Tomato Logistics Platform.

This module is the future home for Flutterwave API calls. For now, it only
returns mock responses and does not make HTTP requests or use any SDK.
"""

try:
    from backend.Flutterwave.payment_gateway import PaymentGateway
except ImportError:
    from backend.Flutterwave.payment_gateway import PaymentGateway


class FlutterwaveGateway(PaymentGateway):
    """
    Represents the Flutterwave payment provider.
    """

    def initialize_payment(self, payment):
  
        return {
            "status": "success",
            "payment_link": (
                "https://flutterwave.test/pay/"
                f"{payment['tx_ref'].lower()}"
            ),
            "tx_ref": payment["tx_ref"],
        }

    def verify_payment(self, tx_ref):

        return {
            "status": "success",
            "payment_status": "PENDING",
            "tx_ref": tx_ref,
        }

    def refund_payment(self, tx_ref):
 
        return {
            "status": "success",
            "payment_status": "REFUNDED",
            "tx_ref": tx_ref,
        }
