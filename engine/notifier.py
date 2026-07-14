"""
Notification module for the Tomato Logistics Platform.

The notifier receives reservation results and creates notification
objects for farmers, transporters, hub operators, and administrators.

It does not send SMS, emails, or write to the database.
"""

import logging
from datetime import datetime

try:
    from engine.logger import EngineLogger
except ImportError:
    try:
        from logger import EngineLogger
    except ImportError:
        EngineLogger = None


class NotificationError(Exception):
    """Raised when notification creation fails."""


class Notifier:
    """
    Creates notification objects after successful reservations and payments.

    The notifier receives trip/payment dictionaries and returns notification
    dictionaries. It does not send SMS; it prepares queued or failed records for
    a future SMS service.
    """

    SUPPORTED_EVENTS = {
        "PAYMENT_PENDING",
        "PAYMENT_SUCCESSFUL",
        "TRIP_RESERVED",
        "TRUCK_DISPATCHED",
        "ARRIVED_AT_HUB",
        "TRIP_COMPLETED",
    }

    def __init__(self, logger=None):
        """
        Create a notifier.

        Receives an optional logger. Returns a notifier that can build event
        notifications for farmers, transporters, hub operators, and admins.
        """
        if logger:
            self.logger = logger
        elif EngineLogger:
            self.logger = EngineLogger()
        else:
            self.logger = logging.getLogger(__name__)

    def create_notifications(self, reservation_results):
        """
        Create notifications from reservation or payment results.

        Receives engine results with trip allocations and returns queued
        notification objects for the events that match each trip.
        """

        self.logger.info("Notification process started.")

        try:
            notifications = []
            failed_notifications = []

            trip_allocations = reservation_results.get("trip_allocations", [])

            for trip in trip_allocations:

                self.validate_trip(trip)
                events = self.get_events_for_trip(trip)

                for event_type in events:
                    event_notifications = self.create_event_notifications(
                        trip,
                        event_type
                    )

                    for notification in event_notifications:
                        if notification.get("status") == "FAILED":
                            failed_notifications.append(notification)
                        else:
                            notifications.append(notification)

            self.logger.info(
                f"{len(notifications)} notifications created."
            )

            self.logger.info("Notification process completed.")

            return {
                "notifications": notifications,
                "failed_notifications": failed_notifications,
                "status": "SUCCESS"
            }

        except Exception as error:
            self.logger.error(f"Notification error: {error}")
            raise

    def create_event_notifications(self, trip, event_type):
        """
        Create notifications for one event.

        Receives a trip and an event type, then returns all role-based
        notification objects needed for that event.
        """
        self.validate_event_type(event_type)

        notifications = []

        farmer_message = self.get_message("FARMER", event_type, trip)
        if farmer_message:
            for farmer_phone in self.get_farmer_phones(trip):
                notifications.append(
                    self.build_notification(
                        "FARMER",
                        trip,
                        event_type,
                        farmer_message,
                        farmer_phone
                    )
                )

        transporter_message = self.get_message("TRANSPORTER", event_type, trip)
        if transporter_message:
            notifications.append(
                self.build_notification(
                    "TRANSPORTER",
                    trip,
                    event_type,
                    transporter_message
                )
            )

        hub_message = self.get_message("HUB_OPERATOR", event_type, trip)
        if hub_message:
            notifications.append(
                self.build_notification(
                    "HUB_OPERATOR",
                    trip,
                    event_type,
                    hub_message
                )
            )

        admin_message = self.get_message("ADMIN", event_type, trip)
        if admin_message:
            notifications.append(
                self.build_notification("ADMIN", trip, event_type, admin_message)
            )

        return notifications

    def get_events_for_trip(self, trip):
        """
        Decide which events apply to a trip.

        Receives one trip dictionary and returns a list of event names that
        should generate notifications now.
        """
        events = []

        if trip.get("status") == "RESERVED":
            events.append("TRIP_RESERVED")

        if trip.get("payment_status") == "PENDING":
            events.append("PAYMENT_PENDING")

        if trip.get("payment_status") == "PAID":
            events.append("PAYMENT_SUCCESSFUL")

        if trip.get("status") == "DISPATCHED":
            events.append("TRUCK_DISPATCHED")

        if trip.get("status") == "ARRIVED_AT_HUB":
            events.append("ARRIVED_AT_HUB")

        if trip.get("status") == "COMPLETED":
            events.append("TRIP_COMPLETED")

        return events

    def build_notification(
        self,
        recipient_type,
        trip,
        event_type,
        message,
        recipient_phone=None
    ):
        """
        Build one notification object.

        Receives a recipient role, trip, event type, and message. Returns the
        queued or failed notification dictionary without sending SMS or email.
        """
        phone = recipient_phone or self.get_recipient_phone(
            recipient_type,
            trip
        )
        created_at = datetime.now()

        if not self.is_valid_phone(phone):
            return {
                "event_type": event_type,
                "recipient_type": recipient_type,
                "recipient_phone": phone,
                "channel": "SMS",
                "message": message,
                "status": "FAILED",
                "delivery_status": "FAILED",
                "retry_count": 0,
                "provider_message_id": None,
                "failure_reason": "INVALID_RECIPIENT_PHONE",
                "created_at": created_at,
                "updated_at": created_at,
                "sent_time": None,
                "related_trip_id": trip.get("allocation_id"),
            }

        return {
            "event_type": event_type,
            "recipient_type": recipient_type,
            "recipient_phone": phone,
            "channel": "SMS",
            "message": message,
            "status": "QUEUED",
            "delivery_status": "QUEUED",
            "retry_count": 0,
            "provider_message_id": None,
            "failure_reason": None,
            "created_at": created_at,
            "updated_at": created_at,
            "sent_time": None,
            # allocation_id is only available after trip persistence.
            "related_trip_id": trip.get("allocation_id")
        }

    def get_farmer_phones(self, trip):
        """
        Get all farmer phone numbers for a trip.

        Receives one trip dictionary and returns every farmer phone available
        on a clustered trip. Falls back to farmer_phone for older data shapes.
        """
        farmer_phones = trip.get("farmer_phones", [])

        if farmer_phones:
            return farmer_phones

        farmer_phone = trip.get("farmer_phone")
        if farmer_phone:
            return [farmer_phone]

        return [None]

    def get_recipient_phone(self, recipient_type, trip):
        """
        Get the phone number for a recipient role.

        Receives a recipient type and trip dictionary. Returns the matching
        phone number if it is available.
        """
        if recipient_type == "FARMER":
            return trip.get("farmer_phone")
        if recipient_type == "TRANSPORTER":
            return trip.get("transporter_phone")
        if recipient_type == "HUB_OPERATOR":
            return trip.get("hub_phone")
        if recipient_type == "ADMIN":
            return trip.get("admin_phone")

        return None

    def get_message(self, recipient_type, event_type, trip):
        """
        Create the correct message for a role and event.

        Receives a recipient role, event type, and trip. Returns message text
        or None when that role should not be notified for the event.
        """
        payment_amount = trip.get("payment_amount")

        messages = {
            "PAYMENT_PENDING": {
                "FARMER": (
                    "Payment is pending for your reserved tomato pickup."
                ),
                "TRANSPORTER": (
                    "A reserved trip is waiting for payment confirmation."
                ),
                "HUB_OPERATOR": (
                    "Incoming delivery is pending payment confirmation."
                ),
                "ADMIN": (
                    "A trip has a pending payment request."
                ),
            },
            "PAYMENT_SUCCESSFUL": {
                "FARMER": (
                    "Your payment has been confirmed successfully."
                ),
                "TRANSPORTER": (
                    "Payment is confirmed for your assigned trip."
                ),
                "HUB_OPERATOR": (
                    "Payment is confirmed for an incoming delivery."
                ),
                "ADMIN": (
                    "A trip payment has been completed successfully."
                ),
            },
            "TRIP_RESERVED": {
                "FARMER": (
                    "Your harvest has been scheduled for pickup."
                ),
                "TRANSPORTER": (
                    "A new transport trip has been assigned to you."
                ),
                "HUB_OPERATOR": (
                    "Incoming tomato delivery has been scheduled."
                ),
                "ADMIN": (
                    "A new coordination trip has been reserved."
                ),
            },
            "TRUCK_DISPATCHED": {
                "FARMER": "Your pickup truck is on the way.",
                "TRANSPORTER": "Dispatch reminder: your assigned trip is active.",
                "HUB_OPERATOR": "A truck has been dispatched toward your hub.",
                "ADMIN": "A truck has been dispatched for a reserved trip.",
            },
            "ARRIVED_AT_HUB": {
                "FARMER": "Your tomatoes have arrived at the cold hub.",
                "TRANSPORTER": "Arrival recorded for your assigned trip.",
                "HUB_OPERATOR": "The assigned truck has arrived at the hub.",
                "ADMIN": "A reserved trip has arrived at the hub.",
            },
            "TRIP_COMPLETED": {
                "FARMER": "Your tomato delivery trip has been completed.",
                "TRANSPORTER": "Your assigned trip has been completed.",
                "HUB_OPERATOR": "The incoming delivery trip has been completed.",
                "ADMIN": "A coordination trip has been completed.",
            },
        }

        message = messages.get(event_type, {}).get(recipient_type)

        if event_type == "PAYMENT_PENDING" and recipient_type == "FARMER":
            if payment_amount is not None:
                message = (
                    "Payment is pending for your reserved tomato pickup. "
                    f"Amount: {payment_amount}."
                )

        return message

    def validate_event_type(self, event_type):
        """
        Check that the event type is supported.

        Receives an event name and raises NotificationError if the event is not
        part of the engine workflow.
        """
        if event_type not in self.SUPPORTED_EVENTS:
            raise NotificationError(f"Unsupported notification event: {event_type}")

    def notify_farmer(self, trip):
        """
        Create a farmer notification for backward compatibility.

        Receives one trip dictionary. Returns one notification dictionary.
        """

        return self.build_notification(
            "FARMER",
            trip,
            "TRIP_RESERVED",
            "Your harvest has been scheduled for pickup.",
            trip.get("farmer_phone")
        )

    def notify_transporter(self, trip):
        """
        Create a transporter notification for backward compatibility.

        Receives one trip dictionary. Returns one notification dictionary.
        """

        return self.build_notification(
            "TRANSPORTER",
            trip,
            "TRIP_RESERVED",
            "A new transport trip has been assigned to you.",
            trip.get("transporter_phone")
        )

    def notify_hub(self, trip):
        """
        Create a cold hub notification for backward compatibility.

        Receives one trip dictionary. Returns one notification dictionary.
        """

        return self.build_notification(
            "HUB_OPERATOR",
            trip,
            "TRIP_RESERVED",
            "Incoming tomato delivery has been scheduled.",
            trip.get("hub_phone")
        )

    def notify_admin(self, trip):
        """
        Create an administrator notification for backward compatibility.

        Receives one trip dictionary. Returns one notification dictionary.
        """

        return self.build_notification(
            "ADMIN",
            trip,
            "TRIP_RESERVED",
            "A new coordination trip has been reserved.",
            trip.get("admin_phone")
        )

    def validate_trip(self, trip):
        """
        Validate a trip before creating notifications.

        Receives one trip dictionary. Returns None or raises NotificationError
        if the trip is missing required identity or status data.
        """

        if not trip.get("truck_id"):
            raise NotificationError("Truck ID is missing.")

        if not trip.get("hub_id"):
            raise NotificationError("Hub ID is missing.")

        allowed_statuses = {
            "RESERVED",
            "DISPATCHED",
            "ARRIVED_AT_HUB",
            "COMPLETED",
        }

        if trip.get("status") not in allowed_statuses:
            raise NotificationError(
                "Notifications can only be created for known trip statuses."
            )

    def is_valid_phone(self, phone):
        """
        Check whether a phone number is usable for SMS.

        Receives a phone value. Returns True for simple local/international
        numbers and False for missing or malformed values.
        """
        if not phone or not isinstance(phone, str):
            return False

        normalized = phone.strip().replace(" ", "").replace("-", "")
        if normalized.startswith("+"):
            normalized = normalized[1:]

        return normalized.isdigit() and 7 <= len(normalized) <= 15
