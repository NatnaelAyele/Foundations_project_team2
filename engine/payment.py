"""
Payment manager for the Tomato Logistics Platform.

The payment manager runs after reservation and before notification. It creates
simple payment records and asks a payment gateway to initialize the payment.
No database queries, real payment links, or external API calls are made here.
"""

import logging

try:
    from gateways.flutterwave import FlutterwaveGateway
    from logger import EngineLogger
except ImportError:
    from engine.gateways.flutterwave import FlutterwaveGateway
    from engine.logger import EngineLogger


class PaymentError(ValueError):
    """Raised when payment data is missing or invalid."""


class PaymentStatus:
    """Stores the payment statuses supported by the engine."""

    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentManager:
    """Controls the payment process after reservation and before notification."""

    def __init__(
        self,
        gateway=None,
        logger=None,
        transport_rate_per_kg=2.0,
        storage_rate_per_kg=1.0,
        currency="SSP",
    ):
       
        self.gateway = gateway or FlutterwaveGateway()
        self.transport_rate_per_kg = transport_rate_per_kg
        self.storage_rate_per_kg = storage_rate_per_kg
        self.currency = currency
        self.payment_counter = 0

        if logger:
            self.logger = logger
        elif EngineLogger:
            self.logger = EngineLogger()
        else:
            self.logger = logging.getLogger(__name__)

    def calculate_transport_cost(self, reservation):
        """Calculate the transport cost for one reserved trip. """
        total_load = self.get_total_load(reservation)
        return total_load * self.transport_rate_per_kg

    def calculate_storage_cost(self, reservation):
        """Calculate the cold storage cost for one reserved trip."""
        total_load = self.get_total_load(reservation)
        return total_load * self.storage_rate_per_kg

    def calculate_total_amount(self, reservation):
        """ Calculate the full amount that should be paid for a reserved trip."""
        transport_cost = self.calculate_transport_cost(reservation)
        storage_cost = self.calculate_storage_cost(reservation)
        return transport_cost + storage_cost

    def create_payment(self, reservation):
        """ Create a local payment record for one reserved trip."""
        self.validate_reservation(reservation)
        self.payment_counter += 1

        payment_id = f"PAY-{self.payment_counter:06d}"
        tx_ref = self.generate_payment_reference()

        return {
            "payment_id": payment_id,
            "allocation_id": self.get_allocation_id(reservation),
            "farmer_id": reservation.get("farmer_id"),
            "amount": self.calculate_total_amount(reservation),
            "currency": self.currency,
            "payment_method": "FLUTTERWAVE",
            "status": PaymentStatus.PENDING,
            "tx_ref": tx_ref,
            "payment_link": None,
        }

    def initialize_payment(self, reservation_results):
        """ Create and initialize payments for all reserved trips. """
        self.logger.info("Payment process started.")

        trip_allocations = reservation_results.get("trip_allocations", [])
        payments = []
        enriched_trips = []

        for trip in trip_allocations:
            payment = self.create_payment(trip)
            gateway_response = self.gateway.initialize_payment(payment)

            if gateway_response.get("status") == "success":
                payment["payment_link"] = gateway_response.get("payment_link")
                payment["tx_ref"] = gateway_response.get(
                    "tx_ref",
                    payment["tx_ref"]
                )
            else:
                self.update_payment_status(payment, PaymentStatus.FAILED)

            payments.append(payment)
            enriched_trips.append(self.add_payment_summary_to_trip(trip, payment))

        payment_results = reservation_results.copy()
        payment_results["trip_allocations"] = enriched_trips
        payment_results["payments"] = payments
        payment_results["payment_status"] = PaymentStatus.PENDING
        payment_results["total_payments"] = len(payments)

        self.logger.info(f"{len(payments)} payments initialized.")
        self.logger.info("Payment process completed.")
        return payment_results

    def verify_payment(self, payment):
        """Verify one payment using the configured gateway. """
        tx_ref = payment.get("tx_ref")
        if not tx_ref:
            raise PaymentError("Payment transaction reference is missing.")

        response = self.gateway.verify_payment(tx_ref)
        new_status = response.get("payment_status", PaymentStatus.PENDING)
        return self.update_payment_status(payment, new_status)

    def refund_payment(self, payment):
        """Request a refund for one payment using the configured gateway."""
        tx_ref = payment.get("tx_ref")
        if not tx_ref:
            raise PaymentError("Payment transaction reference is missing.")

        response = self.gateway.refund_payment(tx_ref)
        new_status = response.get("payment_status", PaymentStatus.REFUNDED)
        return self.update_payment_status(payment, new_status)

    def update_payment_status(self, payment, status):
        """ Change the status of one payment record. """
        allowed_statuses = {
            PaymentStatus.PENDING,
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED,
        }

        if status not in allowed_statuses:
            raise PaymentError("Unsupported payment status.")

        payment["status"] = status
        return payment

    def add_payment_summary_to_trip(self, trip, payment):
        """ Add simple payment details to a reserved trip."""
        enriched_trip = trip.copy()
        enriched_trip["payment_id"] = payment["payment_id"]
        enriched_trip["payment_status"] = payment["status"]
        enriched_trip["payment_amount"] = payment["amount"]
        enriched_trip["payment_reference"] = payment["tx_ref"]
        enriched_trip["payment_link"] = payment["payment_link"]
        return enriched_trip

    def generate_payment_reference(self):
        """ Generate a simple transaction reference. """
        return f"TX-{self.payment_counter:06d}"

    def get_allocation_id(self, reservation):
        """ Get the allocation ID used by the payment record. """
        allocation_id = reservation.get("allocation_id")
        if allocation_id:
            return allocation_id

        truck_id = reservation.get("truck_id")
        hub_id = reservation.get("hub_id")
        return f"TEMP-TRIP-{truck_id}-{hub_id}"

    def get_total_load(self, reservation):
        """ Read and validate the total load for one reserved trip. """
        total_load = reservation.get("total_load_kg")

        if total_load is None:
            raise PaymentError("Total load is missing.")

        try:
            total_load = float(total_load)
        except (TypeError, ValueError) as error:
            raise PaymentError("Total load must be a number.") from error

        if total_load <= 0:
            raise PaymentError("Total load must be greater than 0 kg.")

        return total_load

    def validate_reservation(self, reservation):
        """ Check that a reserved trip has the data needed for payment. """
        if reservation.get("status") != "RESERVED":
            raise PaymentError("Payments can only be created for reserved trips.")

        if not reservation.get("truck_id"):
            raise PaymentError("Truck ID is missing.")

        if not reservation.get("hub_id"):
            raise PaymentError("Hub ID is missing.")

        self.get_total_load(reservation)
