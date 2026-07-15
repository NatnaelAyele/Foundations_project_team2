"""
Planner module for the Tomato Logistics Platform.

The planner receives successful truck and hub matches, then creates plain
Python dictionaries that match the database schema. It does not save anything
to PostgreSQL, reserve resources, or send notifications.
"""

import logging
from datetime import datetime, timedelta

try:
    from backend.engine.logger import EngineLogger
except ImportError:
    EngineLogger = None


class PlannerError(ValueError):
    """Raised when the planner receives invalid data."""


class Planner:
    """
    Creates planned trip and forecast allocation dictionaries.

    The planner receives successful matches from Group 2 and returns plain
    dictionaries. It does not save to the database; it only prepares records
    that a future service layer can insert in the right order.
    """

    def __init__(self, logger=None):
        """
        Create a planner instance.

        Receives an optional logger. Returns a Planner that can turn matched
        trucks, hubs, and forecast clusters into planned trip records.
        """
        if logger:
            self.logger = logger
        elif EngineLogger:
            self.logger = EngineLogger()
        else:
            self.logger = logging.getLogger(__name__)

    def plan_trips(self, plan_id: int, successful_matches: list) -> dict:
        """
        Create trip and forecast allocations from successful matches.

        Receives a database plan_id when available and a list of successful
        Group 2 matches. Returns trip_allocations first, because trips must be
        inserted before forecast_allocations can receive allocation_id.
        """
        self.logger.info("Planning started.")
        self.logger.info(f"Number of successful matches: {len(successful_matches)}.")

        try:
            trip_allocations = []
            forecast_allocations = []

            for index, match in enumerate(successful_matches, start=1):
                # Create one trip allocation.
                temporary_trip_key = self.create_temporary_trip_key(index)
                trip = self.create_trip_allocation(
                    plan_id,
                    match,
                    temporary_trip_key
                )
                trip_allocations.append(trip)
                self.logger.info("Trip allocation created.")

                # Forecast allocations wait for the database allocation_id.
                allocations = self.create_forecast_allocations(
                    match,
                    temporary_trip_key
                )
                forecast_allocations.extend(allocations)
                self.logger.info(
                    f"Forecast allocations created: {len(allocations)}."
                )

            # Return the planning results.
            self.logger.info("Planning completed.")
            self.logger.info(f"Number of trips created: {len(trip_allocations)}.")
            self.logger.info(
                "Number of forecast allocations created: "
                f"{len(forecast_allocations)}."
            )

            return {
                "trip_allocations": trip_allocations,
                "forecast_allocations": forecast_allocations,
                "persistence_order": [
                    "insert trip_allocations",
                    "copy generated allocation_id to forecast_allocations",
                    "insert forecast_allocations",
                ],
            }

        except Exception as error:
            self.logger.error(f"Planning error: {error}")
            raise

    def create_trip_allocation(
        self,
        plan_id: int,
        match: dict,
        temporary_trip_key=None
    ) -> dict:
        """
        Create one planned trip allocation dictionary.

        Receives a plan_id, one successful match, and an optional temporary
        trip key. Returns a trip record shaped for the trip_allocations table.
        allocation_id is None because PostgreSQL will generate it.
        """
        self.validate_allocation(match)

        pickup_time = self.estimate_pickup_time()
        arrival_time = self.estimate_arrival_time(pickup_time)

        return {
            "allocation_id": match.get("allocation_id"),
            "plan_id": plan_id,
            "temporary_plan_pending": plan_id is None,
            "temporary_trip_key": temporary_trip_key,
            "truck_id": match["truck_id"],
            "hub_id": match["hub_id"],
            "sector_id": match["sector_id"],
            "total_load_kg": self.get_total_load(match),
            "truck_capacity_kg": self.get_truck_capacity(match),
            "available_capacity_kg": self.get_hub_capacity(match),
            "pickup_start": pickup_time,
            "estimated_hub_arrival": arrival_time,
            "status": "SCHEDULED",
            "persistence_status": "PENDING_DATABASE_INSERT",
        }

    def create_forecast_allocations(
        self,
        match: dict,
        temporary_trip_key=None
    ) -> list:
        """
        Create one forecast allocation for each forecast in the cluster.

        Receives a successful match and optional temporary trip key. Returns
        records that can later receive the generated trip allocation_id after
        the trip row is inserted.
        """
        forecasts = self.get_forecasts(match)
        allocations = []

        for forecast in forecasts:
            if not forecast.get("forecast_id"):
                raise PlannerError("Forecast ID is missing.")

            quantity = forecast.get("allocated_quantity_kg")
            if quantity is None:
                quantity = forecast.get("quantity_kg")
            if quantity is None:
                quantity = forecast.get("quantity")

            quantity = self.to_number(quantity, "Forecast quantity")

            if quantity <= 0:
                raise PlannerError("Forecast quantity must be greater than 0.")

            allocations.append(
                {
                    "allocation_id": match.get("allocation_id"),
                    "temporary_trip_key": temporary_trip_key,
                    "persistence_status": "WAITING_FOR_TRIP_ALLOCATION_ID",
                    "forecast_id": forecast["forecast_id"],
                    "allocated_quantity_kg": quantity,
                }
            )

        return allocations

    def estimate_pickup_time(self) -> datetime:
        """
        Estimate when the truck should start pickup.

        Receives no input. Returns a datetime used for pickup_start.
        """
        return datetime.now()

    def estimate_arrival_time(self, pickup_time: datetime) -> datetime:
        """
        Estimate when the truck should arrive at the hub.

        Receives a pickup datetime. Returns the estimated hub arrival datetime.
        """
        return pickup_time + timedelta(hours=2)

    def validate_allocation(self, match: dict) -> None:
        """
        Check that the match has enough data to create a trip.

        Receives one match dictionary. Returns None or raises PlannerError with
        a clear reason if required fields are missing or invalid.
        """
        truck_id = match.get("truck_id")
        hub_id = match.get("hub_id")
        sector_id = match.get("sector_id")
        forecasts = self.get_forecasts(match)
        total_load = self.get_total_load(match)
        truck_capacity = self.get_truck_capacity(match)
        hub_capacity = self.get_hub_capacity(match)

        if not truck_id:
            raise PlannerError("Truck ID is missing.")
        if not hub_id:
            raise PlannerError("Hub ID is missing.")
        if not sector_id:
            raise PlannerError("Sector ID is missing.")
        if not forecasts:
            raise PlannerError("Cluster must contain at least one forecast.")
        if total_load <= 0:
            raise PlannerError("Total load must be greater than 0 kg.")
        if truck_capacity < total_load:
            raise PlannerError("Truck capacity is not enough for this trip.")
        if hub_capacity < total_load:
            raise PlannerError("Hub capacity is not enough for this trip.")

    def get_forecasts(self, match: dict) -> list:
        """
        Get forecasts from the match or from its cluster.

        Receives one match dictionary. Returns the list of forecasts that will
        be connected to the planned trip.
        """
        if "forecasts" in match:
            forecasts = match["forecasts"]
        elif "cluster" in match and "forecasts" in match["cluster"]:
            forecasts = match["cluster"]["forecasts"]
        else:
            raise PlannerError("No forecasts found in the match.")

        if not isinstance(forecasts, list):
            raise PlannerError("Forecasts must be provided as a list.")

        return forecasts

    def get_total_load(self, match: dict) -> float:
        """
        Get the total load for the trip.

        Receives one match dictionary. Returns the total load as a float.
        """
        if "total_load_kg" in match:
            return self.to_number(match["total_load_kg"], "Total load")

        if "cluster" in match and "total_load_kg" in match["cluster"]:
            return self.to_number(match["cluster"]["total_load_kg"], "Total load")

        total_load = 0
        for forecast in self.get_forecasts(match):
            if "quantity_kg" in forecast:
                total_load += self.to_number(
                    forecast["quantity_kg"],
                    "Forecast quantity"
                )
            elif "quantity" in forecast:
                total_load += self.to_number(
                    forecast["quantity"],
                    "Forecast quantity"
                )
            else:
                raise PlannerError("Forecast quantity is missing.")

        return total_load

    def get_truck_capacity(self, match: dict) -> float:
        """
        Get the truck capacity from the match.

        Receives one match dictionary. Returns truck capacity in kilograms.
        """
        if "truck_capacity_kg" in match:
            return self.to_number(match["truck_capacity_kg"], "Truck capacity")
        if "capacity_kg" in match:
            return self.to_number(match["capacity_kg"], "Truck capacity")
        if "truck" in match and "capacity_kg" in match["truck"]:
            return self.to_number(match["truck"]["capacity_kg"], "Truck capacity")

        raise PlannerError("Truck capacity is missing.")

    def get_hub_capacity(self, match: dict) -> float:
        """
        Get the hub available capacity from the match.

        Receives one match dictionary. Returns available hub capacity in kg.
        """
        if "hub_available_capacity_kg" in match:
            return self.to_number(
                match["hub_available_capacity_kg"],
                "Hub capacity"
            )
        if "available_capacity_kg" in match:
            return self.to_number(match["available_capacity_kg"], "Hub capacity")
        if "hub" in match and "available_capacity_kg" in match["hub"]:
            return self.to_number(
                match["hub"]["available_capacity_kg"],
                "Hub capacity"
            )

        raise PlannerError("Hub capacity is missing.")

    def to_number(self, value, field_name: str) -> float:
        """
        Convert a value to a number.

        Receives any value and a field name for error messages. Returns a float
        or raises PlannerError if conversion fails.
        """
        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise PlannerError(f"{field_name} must be a number.") from error

    def create_temporary_trip_key(self, index: int) -> str:
        """
        Create a temporary trip key for linking unsaved records.

        Receives the trip number inside one planning run. Returns a readable key
        that the service layer can replace with the real allocation_id.
        """
        return f"TEMP-TRIP-{index}"
