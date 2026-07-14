"""
HubMatcher (Group 2 - Engine Person 2)

Finds a cold_hub with enough available_capacity_kg for a cluster that
already has a matched truck, then assembles the full payload the
Planner (Group 3) needs to create a trip - so planner.py doesn't have
to re-fetch anything.

Interface contract (engine_integration_guide.md):
    class HubMatcher:
        def match(self, truck_matches): ...

Input (from TruckMatcher):
    [
        {"cluster": {...}, "truck": {"truck_id": 5, "capacity_kg": 1000}},
        # or an exclusion marker from TruckMatcher, passed through unchanged
        {"cluster": {...}, "excluded": True, "reason_code": "NO_TRUCK"},
        ...
    ]

Output: one entry per input. Either the full Planner payload (matching
the exact shape in the integration guide) or an exclusion marker with
reason_code NO_HUB_CAPACITY.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_

# Adjust this import path to match wherever your SQLAlchemy models live.
from models import ColdHub, Truck, Transporter, User

HUB_OPEN_STATUS = "OPEN"
ADMIN_PHONE_FALLBACK = "0788000000"  # placeholder - replace with real config/DB value


class HubMatcher:
    def __init__(self, db: Session):
        self.db = db

    def match(self, truck_matches):
        results = []
        for entry in truck_matches:
            # Pass through exclusions from TruckMatcher untouched.
            if entry.get("excluded"):
                results.append(entry)
                continue

            cluster = entry["cluster"]
            truck_info = entry["truck"]
            sector_id = cluster["sector_id"]
            required_kg = cluster["total_load_kg"]

            hub = self._find_hub(sector_id, required_kg)

            if hub is None:
                results.append({
                    "cluster": cluster,
                    "excluded": True,
                    "reason_code": "NO_HUB_CAPACITY",
                })
                continue

            results.append(self._build_payload(cluster, truck_info, hub))

        return results

    def _find_hub(self, sector_id, required_kg):
        """
        Picks the tightest-fitting open hub with enough room, so we don't
        needlessly reserve a huge hub's capacity for a small cluster.
        """
        return (
            self.db.query(ColdHub)
            .filter(
                and_(
                    ColdHub.sector_id == sector_id,
                    ColdHub.operating_status == HUB_OPEN_STATUS,
                    ColdHub.available_capacity_kg >= required_kg,
                )
            )
            .order_by(ColdHub.available_capacity_kg.asc())
            .first()
        )

    def _build_payload(self, cluster, truck_info, hub):
        truck = self.db.query(Truck).get(truck_info["truck_id"])
        transporter = (
            self.db.query(Transporter).get(truck.transporter_id) if truck else None
        )
        admin = self.db.query(User).filter(User.role == "ADMIN").first()

        forecasts = [
            {
                "forecast_id": f["forecast_id"],
                "quantity_kg": f["quantity_kg"],
                "farmer_id": f["farmer_id"],
                "farmer_phone": f["farmer_phone"],
            }
            for f in cluster["forecasts"]
        ]

        return {
            "truck_id": truck.truck_id,
            "hub_id": hub.hub_id,
            "sector_id": cluster["sector_id"],
            "cluster": {
                "sector_id": cluster["sector_id"],
                "total_load_kg": cluster["total_load_kg"],
                "forecasts": forecasts,
            },
            "truck": {
                "truck_id": truck.truck_id,
                "capacity_kg": truck.capacity_kg,
            },
            "hub": {
                "hub_id": hub.hub_id,
                "available_capacity_kg": hub.available_capacity_kg,
            },
            "transporter_phone": transporter.phone if transporter else None,
            "hub_phone": hub.phone,
            "admin_phone": ADMIN_PHONE_FALLBACK,
        }
