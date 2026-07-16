"""
TruckMatcher (Group 2 - Engine Person 2)

Finds an available truck in the cluster's sector with enough capacity_kg
to carry the cluster's total demand.

Interface contract (engine_integration_guide.md):
    class TruckMatcher:
        def match(self, demand_results): ...

Input (from Group 1's DemandAnalyzer):
    [
        {"cluster": {...}, "required_capacity_kg": 800},
        ...
    ]

Output:
    One entry per demand_result, either a truck match or an exclusion
    marker so Group 3's logger can record a NO_TRUCK exclusion.

    Matched:
        {
            "cluster": {...},
            "truck": {"truck_id": 5, "capacity_kg": 1000}
        }

    Not matched:
        {
            "cluster": {...},
            "excluded": True,
            "reason_code": "NO_TRUCK"
        }
"""

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .exclusion_logger import ExclusionLogger

TRUCK_AVAILABLE_STATUS = "AVAILABLE"


class TruckMatcher:
    """
    Matches demand records to available trucks.

    The matcher receives demand from DemandAnalyzer and selects the smallest
    available truck that can carry each cluster load. If no truck is found, it
    records NO_TRUCK exclusions and allows the remaining clusters to continue.
    """

    def __init__(self, db: Session, truck_model=None, exclusion_logger=None):
        """
        Create a truck matcher.

        Receives a SQLAlchemy session, optional Truck model, and optional
        exclusion logger. Returns a matcher ready to process demand records.
        """
        self.db = db
        self.Truck = truck_model or self.load_truck_model()
        self.exclusion_logger = exclusion_logger or ExclusionLogger()

    def match(self, demand_results):
        """
        Match demand records to trucks.

        Receives demand dictionaries from DemandAnalyzer. Returns one result per
        demand: either a Planner-ready truck match or an excluded record.
        """
        results = []
        for demand in demand_results:
            try:
                self.validate_demand(demand)
                cluster = demand["cluster"]
                sector_id = demand.get("sector_id") or cluster["sector_id"]
                required_kg = demand["required_capacity_kg"]
            except (KeyError, ValueError) as error:
                cluster = demand.get("cluster", {})
                exclusions = self.exclusion_logger.log_cluster(
                    cluster,
                    "INVALID_DEMAND",
                    str(error),
                    "TRUCK_MATCHING",
                )
                results.append({
                    "cluster": cluster,
                    "excluded": True,
                    "reason_code": "INVALID_DEMAND",
                    "description": str(error),
                    "exclusions": exclusions,
                })
                continue

            truck = self._find_truck(sector_id, required_kg)

            if truck is None:
                exclusions = self.exclusion_logger.log_cluster(
                    cluster,
                    "NO_TRUCK",
                    (
                        "No available truck in this sector can carry "
                        f"{required_kg} kg."
                    ),
                    "TRUCK_MATCHING",
                )
                results.append({
                    "cluster": cluster,
                    "excluded": True,
                    "reason_code": "NO_TRUCK",
                    "description": "No available truck with enough capacity.",
                    "exclusions": exclusions,
                })
                continue

            results.append({
                "truck_id": truck.truck_id,
                "truck_capacity_kg": float(truck.capacity_kg),
                "sector_id": sector_id,
                "required_capacity_kg": required_kg,
                "cluster": cluster,
                "truck": {
                    "truck_id": truck.truck_id,
                    "capacity_kg": float(truck.capacity_kg),
                },
                "excluded": False,
            })

        return results

    def _find_truck(self, sector_id, required_kg):
        """
        Picks the smallest available truck that still meets demand, so a
        small cluster doesn't tie up a large truck another cluster needs.
        """
        return (
            self.db.query(self.Truck)
            .filter(
                and_(
                    self.Truck.sector_id == sector_id,
                    self.Truck.status == TRUCK_AVAILABLE_STATUS,
                    self.Truck.capacity_kg >= required_kg,
                )
            )
            .order_by(self.Truck.capacity_kg.asc())
            .first()
        )

    def validate_demand(self, demand):
        """
        Validate one demand record before matching.

        Receives a demand dictionary. Returns None or raises ValueError when the
        demand cannot be matched safely.
        """
        if not isinstance(demand, dict):
            raise ValueError("Demand record must be a dictionary.")

        cluster = demand.get("cluster")
        if not isinstance(cluster, dict):
            raise ValueError("Demand record must include a cluster dictionary.")

        sector_id = demand.get("sector_id") or cluster.get("sector_id")
        if not sector_id:
            raise ValueError("sector_id is missing from demand record.")

        required_kg = demand.get("required_capacity_kg")
        if required_kg is None:
            raise ValueError("required_capacity_kg is missing.")

        if float(required_kg) <= 0:
            raise ValueError("required_capacity_kg must be greater than zero.")

    def load_truck_model(self):
        """
        Load the shared Truck SQLAlchemy model.

        Receives no input. Returns the Truck model from the project model
        package. If the project model has not been created yet, raises an
        ImportError with clear setup guidance.
        """
        try:
            from backend.models import Truck
            return Truck
        except ImportError:
            pass

        try:
            from models import Truck
            return Truck
        except ImportError as error:
            raise ImportError(
                "TruckMatcher needs a shared Truck SQLAlchemy model. Create "
                "backend.models.Truck or pass truck_model=Truck when creating "
                "TruckMatcher."
            ) from error
