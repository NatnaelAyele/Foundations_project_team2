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

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .exclusion_logger import ExclusionLogger

HUB_OPEN_STATUS = "OPEN"
ADMIN_PHONE_FALLBACK = None


class HubMatcher:
    """
    Matches truck matches to cold hubs.

    The matcher receives successful truck matches and finds the smallest open
    hub that can store the cluster load. If no hub is available, it records
    NO_HUB_CAPACITY exclusions and continues with other matches.
    """

    def __init__(
        self,
        db: Session,
        cold_hub_model=None,
        truck_model=None,
        transporter_model=None,
        user_model=None,
        exclusion_logger=None,
    ):
        """
        Create a hub matcher.

        Receives a SQLAlchemy session, optional model classes, and optional
        exclusion logger. Returns a matcher ready to process truck matches.
        """
        self.db = db
        if all([cold_hub_model, truck_model, transporter_model, user_model]):
            models = {}
        else:
            models = self.load_models()
        self.ColdHub = cold_hub_model or models["ColdHub"]
        self.Truck = truck_model or models["Truck"]
        self.Transporter = transporter_model or models["Transporter"]
        self.User = user_model or models["User"]
        self.exclusion_logger = exclusion_logger or ExclusionLogger()

    def match(self, truck_matches):
        """
        Match truck results to cold hubs.

        Receives truck match dictionaries. Returns Planner-ready hub payloads or
        exclusion records for matches that cannot continue.
        """
        results = []
        for entry in truck_matches:
            # Pass through exclusions from TruckMatcher untouched.
            if entry.get("excluded"):
                results.append(entry)
                continue

            try:
                self.validate_truck_match(entry)
                cluster = entry["cluster"]
                truck_info = entry["truck"]
                sector_id = entry.get("sector_id") or cluster["sector_id"]
                required_kg = entry.get("required_capacity_kg")
                if required_kg is None:
                    required_kg = cluster["total_load_kg"]
            except (KeyError, ValueError) as error:
                cluster = entry.get("cluster", {})
                exclusions = self.exclusion_logger.log_cluster(
                    cluster,
                    "INVALID_CLUSTER",
                    str(error),
                    "HUB_MATCHING",
                )
                results.append({
                    "cluster": cluster,
                    "excluded": True,
                    "reason_code": "INVALID_CLUSTER",
                    "description": str(error),
                    "exclusions": exclusions,
                })
                continue

            hub = self._find_hub(sector_id, required_kg)

            if hub is None:
                exclusions = self.exclusion_logger.log_cluster(
                    cluster,
                    "NO_HUB_CAPACITY",
                    (
                        "No open hub in this sector has at least "
                        f"{required_kg} kg available capacity."
                    ),
                    "HUB_MATCHING",
                )
                results.append({
                    "cluster": cluster,
                    "excluded": True,
                    "reason_code": "NO_HUB_CAPACITY",
                    "description": "No open hub with enough available capacity.",
                    "exclusions": exclusions,
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
            self.db.query(self.ColdHub)
            .filter(
                and_(
                    self.ColdHub.sector_id == sector_id,
                    self.ColdHub.operating_status == HUB_OPEN_STATUS,
                    self.ColdHub.available_capacity_kg >= required_kg,
                )
            )
            .order_by(self.ColdHub.available_capacity_kg.asc())
            .first()
        )

    def _build_payload(self, cluster, truck_info, hub):
        """
        Build the Planner payload for a matched truck and hub.

        Receives a cluster, truck information, and hub ORM object. Returns a
        dictionary with all fields Planner needs for trip creation.
        """
        truck = self.get_by_id(self.Truck, truck_info["truck_id"])
        transporter = (
            self.get_by_id(self.Transporter, truck.transporter_id)
            if truck else None
        )
        admin = self.db.query(self.User).filter(self.User.role == "ADMIN").first()

        forecasts = [
            {
                "forecast_id": f["forecast_id"],
                "quantity_kg": f["quantity_kg"],
                "quantity": f.get("quantity", f["quantity_kg"]),
                "farmer_id": f["farmer_id"],
                "farmer_phone": f["farmer_phone"],
                "sector_id": f.get("sector_id", cluster["sector_id"]),
                "harvest_date": f.get("harvest_date"),
                "crop_type": f.get("crop_type", cluster.get("crop_type", "TOMATO")),
            }
            for f in cluster["forecasts"]
        ]

        return {
            "truck_id": truck.truck_id,
            "truck_capacity_kg": float(truck.capacity_kg),
            "hub_id": hub.hub_id,
            "hub_capacity_kg": float(hub.available_capacity_kg),
            "available_capacity_kg": float(hub.available_capacity_kg),
            "sector_id": cluster["sector_id"],
            "total_load_kg": cluster["total_load_kg"],
            "forecasts": forecasts,
            "cluster": {
                "cluster_id": cluster.get("cluster_id"),
                "sector_id": cluster["sector_id"],
                "total_load_kg": cluster["total_load_kg"],
                "crop_type": cluster.get("crop_type", "TOMATO"),
                "forecasts": forecasts,
            },
            "truck": {
                "truck_id": truck.truck_id,
                "capacity_kg": float(truck.capacity_kg),
            },
            "hub": {
                "hub_id": hub.hub_id,
                "available_capacity_kg": float(hub.available_capacity_kg),
                "capacity_kg": float(hub.available_capacity_kg),
            },
            "transporter_phone": transporter.phone if transporter else None,
            "hub_phone": hub.phone,
            # Prefer the real admin user phone when the model has one. If the
            # current User model does not store phone yet, leave this as None so
            # Notifier can safely record a failed recipient instead of sending
            # to a fake number.
            "admin_phone": getattr(admin, "phone", ADMIN_PHONE_FALLBACK),
            "excluded": False,
        }

    def validate_truck_match(self, entry):
        """
        Validate one truck match before hub matching.

        Receives a truck match dictionary. Returns None or raises ValueError if
        hub matching cannot safely continue.
        """
        if not isinstance(entry, dict):
            raise ValueError("Truck match must be a dictionary.")

        cluster = entry.get("cluster")
        if not isinstance(cluster, dict):
            raise ValueError("Truck match must include a cluster dictionary.")

        truck = entry.get("truck")
        if not isinstance(truck, dict):
            raise ValueError("Truck match must include truck information.")

        if not truck.get("truck_id"):
            raise ValueError("truck_id is missing from truck match.")

        if not (entry.get("sector_id") or cluster.get("sector_id")):
            raise ValueError("sector_id is missing from truck match.")

        required_kg = entry.get("required_capacity_kg")
        if required_kg is None:
            required_kg = cluster.get("total_load_kg")

        if required_kg is None or float(required_kg) <= 0:
            raise ValueError("required hub capacity must be greater than zero.")

    def get_by_id(self, model, object_id):
        """
        Load one ORM object by primary key.

        Receives a model class and ID. Returns the matching ORM object or None.
        """
        if hasattr(self.db, "get"):
            return self.db.get(model, object_id)
        return self.db.query(model).get(object_id)

    def load_models(self):
        """
        Load shared SQLAlchemy model classes.

        Receives no input. Returns model classes from the project model package.
        If the shared models are not available yet, raises an ImportError with
        clear setup guidance.
        """
        try:
            from backend.models import ColdHub, Transporter, Truck, User
            return {
                "ColdHub": ColdHub,
                "Truck": Truck,
                "Transporter": Transporter,
                "User": User,
            }
        except ImportError:
            pass

        try:
            from models import ColdHub, Transporter, Truck, User
            return {
                "ColdHub": ColdHub,
                "Truck": Truck,
                "Transporter": Transporter,
                "User": User,
            }
        except ImportError as error:
            raise ImportError(
                "HubMatcher needs shared ColdHub, Truck, Transporter, and "
                "User SQLAlchemy models. Create backend.models or pass the "
                "model classes when creating HubMatcher."
            ) from error
