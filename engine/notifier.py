"""
Notification module for the Tomato Logistics Platform.

The notifier receives reservation results and creates notification
objects for farmers, transporters, hub operators, and administrators.

It does not send SMS, emails, or write to the database.
"""

import logging

try:
    from logger import EngineLogger
except ImportError:
    EngineLogger = None


class NotificationError(Exception):
    """Raised when notification creation fails."""


class Notifier:
    """Creates notification objects after successful reservations."""

    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        elif EngineLogger:
            self.logger = EngineLogger()
        else:
            self.logger = logging.getLogger(__name__)

    def create_notifications(self, reservation_results):
        """
        Create notifications from reservation results.
        """

        self.logger.info("Notification process started.")

        try:
            notifications = []

            trip_allocations = reservation_results.get("trip_allocations", [])

            for trip in trip_allocations:

                self.validate_trip(trip)

                notifications.append(
                    self.notify_farmer(trip)
                )

                notifications.append(
                    self.notify_transporter(trip)
                )

                notifications.append(
                    self.notify_hub(trip)
                )

                notifications.append(
                    self.notify_admin(trip)
                )

            self.logger.info(
                f"{len(notifications)} notifications created."
            )

            self.logger.info("Notification process completed.")

            return {
                "notifications": notifications,
                "status": "SUCCESS"
            }

        except Exception as error:
            self.logger.error(f"Notification error: {error}")
            raise

    def notify_farmer(self, trip):
        """Create a farmer notification."""

        return {
            "recipient_type": "FARMER",
            "recipient_phone": trip.get("farmer_phone"),
            "channel": "SMS",
            "message": "Your harvest has been scheduled for pickup.",
            "status": "QUEUED",
            "sent_time": None,
            # allocation_id is only available after trip persistence.
            "related_trip_id": trip.get("allocation_id")
        }

    def notify_transporter(self, trip):
        """Create a transporter notification."""

        return {
            "recipient_type": "TRANSPORTER",
            "recipient_phone": trip.get("transporter_phone"),
            "channel": "SMS",
            "message": "A new transport trip has been assigned to you.",
            "status": "QUEUED",
            "sent_time": None,
            # allocation_id is only available after trip persistence.
            "related_trip_id": trip.get("allocation_id")
        }

    def notify_hub(self, trip):
        """Create a cold hub notification."""

        return {
            "recipient_type": "HUB_OPERATOR",
            "recipient_phone": trip.get("hub_phone"),
            "channel": "SMS",
            "message": "Incoming tomato delivery has been scheduled.",
            "status": "QUEUED",
            "sent_time": None,
            # allocation_id is only available after trip persistence.
            "related_trip_id": trip.get("allocation_id")
        }

    def notify_admin(self, trip):
        """Create an administrator notification."""

        return {
            "recipient_type": "ADMIN",
            "recipient_phone": trip.get("admin_phone"),
            "channel": "SMS",
            "message": "A new coordination trip has been reserved.",
            "status": "QUEUED",
            "sent_time": None,
            # allocation_id is only available after trip persistence.
            "related_trip_id": trip.get("allocation_id")
        }

    def validate_trip(self, trip):
        """Validate the trip before creating notifications."""

        if not trip.get("truck_id"):
            raise NotificationError("Truck ID is missing.")

        if not trip.get("hub_id"):
            raise NotificationError("Hub ID is missing.")

        if trip.get("status") != "RESERVED":
            raise NotificationError(
                "Notifications can only be created for reserved trips."
            )
