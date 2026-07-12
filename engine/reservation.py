"""
Reservation module for the Tomato Logistics Platform.

The reservation manager receives the planning results from planner.py and
marks the assigned truck, hub capacity, and trip as reserved. It only works
with Python dictionaries. It does not connect to the database.
"""

import logging
from datetime import datetime

try:
    from logger import EngineLogger
except ImportError:
    EngineLogger = None


class ReservationError(ValueError):
    """Raised when a trip cannot be reserved."""


class ReservationManager:
    """Reserves trucks and hub capacity for planned trips."""

    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        elif EngineLogger:
            self.logger = EngineLogger()
        else:
            self.logger = logging.getLogger(__name__)

    def reserve(self, planning_results: dict) -> dict:
        """Reserve resources for every trip allocation."""
        self.logger.info("Reservation started.")

        try:
            reserved_trips = []
            trip_allocations = planning_results.get("trip_allocations", [])
            forecast_allocations = planning_results.get("forecast_allocations", [])

            for trip in trip_allocations:
                # Work on a copy so the original planning result stays unchanged.
                reserved_trip = trip.copy()

                # Reserve the resources needed for this trip.
                self.validate_reservation(reserved_trip)
                self.reserve_truck(reserved_trip)
                self.reserve_hub(reserved_trip)
                self.update_trip_status(reserved_trip)
                reserved_trip["reserved_at"] = datetime.now()

                reserved_trips.append(reserved_trip)

            self.logger.info("Reservation completed.")
            self.logger.info(f"{len(reserved_trips)} trips reserved successfully.")

            return {
                "trip_allocations": reserved_trips,
                "forecast_allocations": forecast_allocations,
                "reservation_status": "SUCCESS",
                "reserved_trips": len(reserved_trips),
            }

        except Exception as error:
            truck_id = None
            hub_id = None

            if "reserved_trip" in locals():
                truck_id = reserved_trip.get("truck_id")
                hub_id = reserved_trip.get("hub_id")

            if truck_id:
                self.logger.error(f"Reservation failed for Truck {truck_id}: {error}")
            elif hub_id:
                self.logger.error(f"Reservation failed for Hub {hub_id}: {error}")
            else:
                self.logger.error(f"Reservation error: {error}")

            raise

    def reserve_truck(self, trip: dict) -> dict:
        """Mark the assigned truck as busy."""
        trip["truck_status"] = "BUSY"
        self.logger.info("Truck reserved.")
        return trip

    def reserve_hub(self, trip: dict) -> dict:
        """Reserve cold hub capacity for the trip load."""
        total_load = float(trip["total_load_kg"])

        # Some callers may include the hub's available capacity in the trip.
        if "available_capacity_kg" in trip:
            available_capacity = float(trip["available_capacity_kg"])

            if available_capacity < total_load:
                raise ReservationError("Hub capacity is not enough.")

            trip["available_capacity_kg"] = available_capacity - total_load

        else:
            self.logger.warning(
                "Hub capacity not provided. Capacity update skipped."
            )

        trip["reserved_capacity_kg"] = total_load
        self.logger.info("Hub reserved.")
        return trip

    def update_trip_status(self, trip: dict) -> dict:
        """Change the trip status from scheduled to reserved."""
        if trip.get("status") != "SCHEDULED":
            raise ReservationError("Only scheduled trips can be marked as reserved.")

        # RESERVED is a temporary engine state used before database persistence.
        # The service layer can map it to the final database status later.
        trip["status"] = "RESERVED"
        self.logger.info("Trip status updated.")
        return trip

    def validate_reservation(self, trip: dict) -> None:
        """Check that a trip can be reserved."""
        truck_id = trip.get("truck_id")
        hub_id = trip.get("hub_id")
        sector_id = trip.get("sector_id")
        status = trip.get("status")
        total_load = trip.get("total_load_kg")

        if not truck_id:
            raise ReservationError("Truck ID is missing.")

        if not hub_id:
            raise ReservationError("Hub ID is missing.")

        if not sector_id:
            raise ReservationError("Sector ID is missing.")

        if status != "SCHEDULED":
            raise ReservationError("Only scheduled trips can be reserved.")

        if total_load is None:
            raise ReservationError("Total load is missing.")

        if float(total_load) <= 0:
            raise ReservationError("Total load must be greater than 0 kg.")
