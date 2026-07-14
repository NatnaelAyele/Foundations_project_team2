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

from sqlalchemy.orm import Session
from sqlalchemy import and_

# Adjust this import path to match wherever your SQLAlchemy models live.
from models import Truck

TRUCK_AVAILABLE_STATUS = "available"


class TruckMatcher:
    def __init__(self, db: Session):
        self.db = db

    def match(self, demand_results):
        results = []
        for demand in demand_results:
            cluster = demand["cluster"]
            sector_id = cluster["sector_id"]
            required_kg = demand["required_capacity_kg"]

            truck = self._find_truck(sector_id, required_kg)

            if truck is None:
                results.append({
                    "cluster": cluster,
                    "excluded": True,
                    "reason_code": "NO_TRUCK",
                })
                continue

            results.append({
                "cluster": cluster,
                "truck": {
                    "truck_id": truck.truck_id,
                    "capacity_kg": truck.capacity_kg,
                },
            })

        return results

    def _find_truck(self, sector_id, required_kg):
        """
        Picks the smallest available truck that still meets demand, so a
        small cluster doesn't tie up a large truck another cluster needs.
        """
        return (
            self.db.query(Truck)
            .filter(
                and_(
                    Truck.sector_id == sector_id,
                    Truck.status == TRUCK_AVAILABLE_STATUS,
                    Truck.capacity_kg >= required_kg,
                )
            )
            .order_by(Truck.capacity_kg.asc())
            .first()
        )
