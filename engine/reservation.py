"""
Reservation module for the Tomato Logistics Platform.

The reservation manager receives the planning results from planner.py and
marks the assigned truck, hub capacity, and trip as reserved.

This module only changes temporary engine dictionaries. Database updates will
be added later in the service layer after the engine output is approved.
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


class ReservationError(ValueError):
    """Raised when a trip cannot be reserved."""


class ReservationManager:
    """
    Reserves trucks and hub capacity for planned trips.

    The manager applies reservation business rules to dictionaries. It does not
    write to PostgreSQL, but it prepares the fields that a future service layer
    should use to update trucks, cold_hubs, and trip_allocations safely.
    """

    ENGINE_RESERVED_STATUS = "RESERVED"
    DATABASE_TRIP_STATUS_AFTER_RESERVATION = "SCHEDULED"
    DATABASE_TRUCK_STATUS_AFTER_RESERVATION = "BUSY"

    def __init__(self, logger=None):
        """
        Create a reservation manager.

        Receives an optional logger. Returns a manager that can validate and
        prepare reservation updates for planned trips.
        """
        if logger:
            self.logger = logger
        elif EngineLogger:
            self.logger = EngineLogger()
        else:
            self.logger = logging.getLogger(__name__)

    def reserve(self, planning_results: dict) -> dict:
        """
        Reserve resources for every trip allocation.

        Receives planner output with trip and forecast allocations. Returns a
        dictionary that separates temporary engine state from future database
        persistence work.
        """
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
                self.prepare_truck_status_update(reserved_trip)
                self.prepare_hub_capacity_update(reserved_trip)
                self.prepare_trip_status_update(reserved_trip)
                reserved_trip["reserved_at"] = datetime.now()
                self.mark_persistence_pending(reserved_trip)

                reserved_trips.append(reserved_trip)

            self.logger.info("Reservation completed.")
            self.logger.info(f"{len(reserved_trips)} trips reserved successfully.")

            return {
                "trip_allocations": reserved_trips,
                "forecast_allocations": forecast_allocations,
                "reservation_status": "SUCCESS",
                "reserved_trips": len(reserved_trips),
                "temporary_engine_state": True,
                "persistence_status": "PENDING_DATABASE_UPDATE",
                "persistence_notes": (
                    "Database updates for trucks, hubs, and trips will be "
                    "handled by the service layer in a future sprint."
                ),
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
        """
        Mark the assigned truck as busy.

        Receives one trip dictionary and returns it with a temporary truck
        reservation status.
        """
        return self.prepare_truck_status_update(trip)

    def reserve_hub(self, trip: dict) -> dict:
        """
        Reserve cold hub capacity for the trip load.

        Receives one trip dictionary and returns it with hub reservation fields
        that can later be persisted to the database.
        """
        return self.prepare_hub_capacity_update(trip)

    def update_trip_status(self, trip: dict) -> dict:
        """
        Change the trip status from scheduled to reserved.

        Receives one scheduled trip and returns it with the engine reservation
        status. The database-compatible status is kept separately.
        """
        return self.prepare_trip_status_update(trip)

    def prepare_truck_status_update(self, trip: dict) -> dict:
        """
        Prepare the future database update for the assigned truck.

        Receives one trip dictionary. Returns it with truck status fields and a
        persistence action that a service layer can later apply to trucks.
        """
        trip["truck_status"] = self.DATABASE_TRUCK_STATUS_AFTER_RESERVATION
        trip["truck_update"] = {
            "table": "trucks",
            "truck_id": trip.get("truck_id"),
            "status": self.DATABASE_TRUCK_STATUS_AFTER_RESERVATION,
        }
        self.logger.info("Truck reservation update prepared.")
        return trip

    def prepare_hub_capacity_update(self, trip: dict) -> dict:
        """
        Prepare the future database update for hub capacity.

        Receives one trip dictionary. Returns it with reserved capacity and
        next available capacity when that capacity was provided by Group 2.
        """
        total_load = float(trip["total_load_kg"])

        # Some callers may include the hub's available capacity in the trip.
        if "available_capacity_kg" in trip:
            available_capacity = float(trip["available_capacity_kg"])

            if available_capacity < total_load:
                raise ReservationError("Hub capacity is not enough.")

            trip["available_capacity_kg"] = available_capacity - total_load
            trip["hub_available_capacity_after_reservation"] = (
                trip["available_capacity_kg"]
            )

        else:
            self.logger.warning(
                "Hub capacity not provided. Capacity update skipped."
            )
            trip["hub_available_capacity_after_reservation"] = None

        trip["reserved_capacity_kg"] = total_load
        trip["hub_status"] = "CAPACITY_RESERVED"
        trip["hub_update"] = {
            "table": "cold_hubs",
            "hub_id": trip.get("hub_id"),
            "reserved_capacity_kg": total_load,
            "available_capacity_kg": trip.get(
                "hub_available_capacity_after_reservation"
            ),
        }
        self.logger.info("Hub capacity update prepared.")
        return trip

    def prepare_trip_status_update(self, trip: dict) -> dict:
        """
        Prepare the future database update for the trip allocation.

        Receives one scheduled trip. Returns it with a reservation event status
        for the engine and a database-compatible trip status for persistence.
        """
        if trip.get("status") != "SCHEDULED":
            raise ReservationError("Only scheduled trips can be marked as reserved.")

        # Keep "status" as RESERVED for existing engine demos and notification
        # events. Store the DB-compatible status separately because the current
        # schema does not include RESERVED in trip_allocations.status.
        trip["status"] = self.ENGINE_RESERVED_STATUS
        trip["database_trip_status"] = self.DATABASE_TRIP_STATUS_AFTER_RESERVATION
        trip["trip_update"] = {
            "table": "trip_allocations",
            "allocation_id": trip.get("allocation_id"),
            "temporary_trip_key": trip.get("temporary_trip_key"),
            "status": self.DATABASE_TRIP_STATUS_AFTER_RESERVATION,
            "reservation_event_status": self.ENGINE_RESERVED_STATUS,
        }
        self.logger.info("Trip reservation update prepared.")
        return trip

    def mark_persistence_pending(self, trip: dict) -> dict:
        """
        Mark future database work without doing database updates.

        Receives a reserved trip and returns it with a small summary that tells
        the service layer what must be saved later.
        """
        trip["persistence_status"] = "PENDING_DATABASE_UPDATE"
        trip["temporary_engine_state"] = True
        trip["database_updates_required"] = [
            "update trucks.status",
            "update cold_hubs.available_capacity_kg",
            "keep or update trip_allocations.status according to schema",
        ]
        trip["reservation_summary"] = {
            "truck_status": trip.get("truck_status"),
            "hub_status": trip.get("hub_status"),
            "trip_status": trip.get("status"),
            "database_trip_status": trip.get("database_trip_status"),
            "reserved_capacity_kg": trip.get("reserved_capacity_kg"),
        }
        return trip

    def validate_reservation(self, trip: dict) -> None:
        """
        Check that a trip can be reserved.

        Receives one trip dictionary and raises ReservationError if required
        reservation data is missing.
        """
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
