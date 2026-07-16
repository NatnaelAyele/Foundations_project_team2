"""
Payment gateway interface for the Tomato Logistics Platform.

This module defines the methods that every payment provider must support.
It does not contain real payment logic. Real providers, such as Flutterwave,
should implement these methods in their own gateway classes.
"""

from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """Defines the contract for all payment gateways."""

    @abstractmethod
    def initialize_payment(self, payment):
        """Start a payment request with a payment provider."""

    @abstractmethod
    def verify_payment(self, tx_ref):
        """Check the status of a payment with a payment provider."""

    @abstractmethod
    def refund_payment(self, tx_ref):
        """Request a refund from a payment provider."""
