
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models.operations import ForecastRequirement, HarvestForecast
from backend.models.provider import Farmer
from .exclusion_logger import ExclusionLogger

# Coordination window - how far ahead a harvest date can be and still get planned.
COORDINATION_WINDOW_DAYS_AHEAD = 3


# Step 2 - not a class in Group 3's guide, just the read that feeds everything else.
# Converts ORM rows into the plain dict shape the classes below (and Group 2/3) expect.
def read_pending_forecasts(db: Session, sector_id: int | None = None) -> list[dict]:
    """
    Read pending harvest forecasts from the database.

    Receives a SQLAlchemy session. Returns dictionaries containing the fields
    needed by validation, matching, planning, payment, and notifications.
    """
    query = (
        db.query(HarvestForecast, Farmer)
        .join(Farmer, Farmer.farmer_id == HarvestForecast.farmer_id)
        .outerjoin(
            ForecastRequirement,
            ForecastRequirement.forecast_id == HarvestForecast.forecast_id,
        )
        .filter(HarvestForecast.status == "PENDING")
    )
    query = query.filter(
        or_(ForecastRequirement.forecast_id.is_(None), ForecastRequirement.needs_transport.is_(True)),
        or_(ForecastRequirement.forecast_id.is_(None), ForecastRequirement.needs_storage.is_(True)),
    )
    if sector_id is not None:
        query = query.filter(Farmer.sector_id == sector_id)

    rows = query.order_by(HarvestForecast.harvest_date.asc()).all()
    forecasts = []
    for forecast, farmer in rows:
        forecasts.append({
            "forecast_id": forecast.forecast_id,
            "farmer_id": forecast.farmer_id,
            "farmer_phone": farmer.phone,
            "quantity_kg": float(forecast.quantity_kg),
            "quantity": float(forecast.quantity_kg),
            "harvest_date": forecast.harvest_date,
            "sector_id": farmer.sector_id,
            "crop_type": "TOMATO",
            "status": forecast.status,
        })
    return forecasts


class Validator:
    """
    Validates harvest forecast dictionaries.

    The validator receives raw pending forecasts and returns only forecasts
    that have the required fields and valid values. Invalid forecasts are
    recorded with the exclusion logger and do not stop the pipeline.
    """

    def __init__(self, today: date | None = None, exclusion_logger=None):
        """
        Create a validator.

        Receives an optional date and exclusion logger. Returns a validator that
        can check forecast dictionaries.
        """
        self.today = today or date.today()
        self.excluded = []
        self.exclusion_logger = exclusion_logger or ExclusionLogger()

    def validate(self, forecasts: list[dict]) -> list[dict]:
        """
        Validate a list of forecasts.

        Receives forecast dictionaries. Returns valid forecasts and records
        INVALID_FORECAST exclusions for the invalid ones.
        """
        valid = []
        self.excluded = []
        for f in forecasts:
            reasons = self._check(f)
            if reasons:
                description = "; ".join(reasons)
                record = self.exclusion_logger.log_forecast(
                    f,
                    "INVALID_FORECAST",
                    description,
                    "VALIDATION",
                )
                self.excluded.append(record)
            else:
                f.setdefault("crop_type", "TOMATO")
                f.setdefault("quantity", f.get("quantity_kg"))
                valid.append(f)
        return valid

    def _check(self, f: dict) -> list[str]:
        """
        Check one forecast for validation errors.

        Receives one forecast dictionary. Returns a list of readable error
        messages. An empty list means the forecast is valid.
        """
        reasons = []

        # Is the farmer registered?
        if not f.get("farmer_id"):
            reasons.append("farmer is not registered")

        # Is the quantity greater than zero?
        try:
            qty = Decimal(str(f.get("quantity_kg")))
            if qty <= 0:
                reasons.append("quantity_kg must be a positive number")
        except (InvalidOperation, TypeError, ValueError):
            reasons.append("quantity_kg is not a valid number")

        # Is the harvest date valid?
        hd = f.get("harvest_date")
        if not isinstance(hd, (date, datetime)):
            reasons.append("harvest_date is not a real date")

        # Is the sector filled in?
        if not f.get("sector_id"):
            reasons.append("sector_id is missing")

        return reasons


class EligibilityChecker:
    """
    Filters valid forecasts by coordination readiness.

    The checker keeps forecasts inside the harvest coordination window and
    records NOT_ELIGIBLE exclusions for forecasts that are valid but not ready.
    """

    def __init__(
        self,
        today: date | None = None,
        window_days_ahead: int = COORDINATION_WINDOW_DAYS_AHEAD,
        exclusion_logger=None,
    ):
        """
        Create an eligibility checker.

        Receives an optional date, coordination window, and exclusion logger.
        Returns a checker for filtering forecasts.
        """
        self.today = today or date.today()
        self.window_days_ahead = window_days_ahead
        self.exclusion_logger = exclusion_logger or ExclusionLogger()

    def filter(self, forecasts: list[dict]) -> list[dict]:
        """
        Keep only forecasts that are ready for coordination.

        Receives valid forecast dictionaries. Returns eligible forecasts and
        records NOT_ELIGIBLE exclusions for forecasts outside the window.
        """
        eligible = []
        for forecast in forecasts:
            ready, reason = self._readiness_result(forecast)
            if ready:
                eligible.append(forecast)
            else:
                self.exclusion_logger.log_forecast(
                    forecast,
                    "NOT_ELIGIBLE",
                    reason,
                    "ELIGIBILITY",
                )
        return eligible

    def _is_ready(self, f: dict) -> bool:
        """
        Check whether one forecast is ready.

        Receives one forecast dictionary. Returns True when it is inside the
        coordination window and has a positive quantity.
        """
        ready, _ = self._readiness_result(f)
        return ready

    def _readiness_result(self, f: dict) -> tuple[bool, str]:
        """
        Explain whether one forecast is ready.

        Receives one forecast dictionary. Returns a tuple of readiness boolean
        and description.
        """
        hd = f.get("harvest_date")
        if not isinstance(hd, (date, datetime)):
            return False, "harvest_date is not a real date"
        hd_date = hd.date() if isinstance(hd, datetime) else hd

        # Harvest date must fall inside the coordination window (not past, not too far ahead).
        within_window = self.today <= hd_date <= self.today + timedelta(days=self.window_days_ahead)

        # Quantity must actually be enough to be worth sending a truck for.
        quantity = f.get("quantity_kg") or 0
        has_quantity = quantity > 0

        if not within_window:
            return False, "harvest_date is outside the coordination window"

        if not has_quantity:
            return False, "quantity_kg must be greater than zero"

        return True, "forecast is eligible"


class ClusteringEngine:
    """
    Groups eligible forecasts by sector.

    The clustering engine receives eligible forecasts and returns clusters that
    can be matched to trucks and hubs. Invalid clusters are recorded without
    stopping other clusters.
    """

    def __init__(self, exclusion_logger=None):
        """
        Create a clustering engine.

        Receives an optional exclusion logger. Returns an engine for creating
        sector-based clusters.
        """
        self.exclusion_logger = exclusion_logger or ExclusionLogger()

    def create_clusters(self, forecasts: list[dict]) -> list[dict]:
        """
        Create sector-based clusters from eligible forecasts.

        Receives eligible forecast dictionaries. Returns cluster dictionaries
        containing sector_id, total_load_kg, crop_type, and forecasts.
        """
        buckets: dict = {}
        for f in forecasts:
            sector_id = f.get("sector_id")
            if not sector_id:
                self.exclusion_logger.log_forecast(
                    f,
                    "INVALID_CLUSTER",
                    "sector_id is missing, so the forecast cannot be clustered",
                    "CLUSTERING",
                )
                continue
            buckets.setdefault(sector_id, []).append(f)

        clusters = []
        for cluster_id, (sector_id, flist) in enumerate(buckets.items(), start=1):
            total_load_kg = sum(f.get("quantity_kg", 0) for f in flist)
            if total_load_kg <= 0:
                self.exclusion_logger.log_cluster(
                    {
                        "cluster_id": cluster_id,
                        "sector_id": sector_id,
                        "forecasts": flist,
                    },
                    "INVALID_CLUSTER",
                    "cluster total_load_kg must be greater than zero",
                    "CLUSTERING",
                )
                continue

            clusters.append({
                "cluster_id": cluster_id,
                "sector_id": sector_id,
                "total_load_kg": total_load_kg,
                "crop_type": "TOMATO",
                "forecasts": flist,
            })
        return clusters


class DemandAnalyzer:
    """
    Converts clusters into demand records for truck matching.

    The analyzer receives valid clusters and returns demand dictionaries that
    TruckMatcher can process. Invalid demand is recorded and skipped.
    """

    def __init__(self, exclusion_logger=None):
        """
        Create a demand analyzer.

        Receives an optional exclusion logger. Returns an analyzer that can
        calculate required transport capacity for clusters.
        """
        self.exclusion_logger = exclusion_logger or ExclusionLogger()

    def calculate(self, clusters: list[dict]) -> list[dict]:
        """
        Calculate truck capacity demand for each cluster.

        Receives cluster dictionaries. Returns demand dictionaries with cluster,
        required_capacity_kg, sector_id, crop_type, and forecasts.
        """
        demand_results = []
        for cluster in clusters:
            required_capacity = cluster.get("total_load_kg")
            if required_capacity is None or required_capacity <= 0:
                self.exclusion_logger.log_cluster(
                    cluster,
                    "INVALID_DEMAND",
                    "required_capacity_kg must be greater than zero",
                    "DEMAND_ANALYSIS",
                )
                continue

            demand_results.append({
                "cluster": cluster,
                "cluster_id": cluster.get("cluster_id"),
                "sector_id": cluster.get("sector_id"),
                "crop_type": cluster.get("crop_type", "TOMATO"),
                "forecasts": cluster.get("forecasts", []),
                "required_capacity_kg": required_capacity,
            })

        return demand_results


# Convenience wrapper chaining my 4 classes together - not part of Group 3's required interface,
# just makes it easy to run all of Group 1's steps in one call for my own testing/demo.
def run_group1_pipeline(db: Session, today: date | None = None) -> list[dict]:
    """
    Run all Group 1 pipeline steps.

    Receives a database session and optional date. Returns demand dictionaries
    that are ready for TruckMatcher. Exclusion records are available from the
    shared ExclusionLogger used by the classes.
    """
    forecasts = read_pending_forecasts(db)

    exclusion_logger = ExclusionLogger()

    validator = Validator(today=today, exclusion_logger=exclusion_logger)
    valid = validator.validate(forecasts)

    eligibility_checker = EligibilityChecker(
        today=today,
        exclusion_logger=exclusion_logger,
    )
    eligible = eligibility_checker.filter(valid)

    clustering_engine = ClusteringEngine(exclusion_logger=exclusion_logger)
    clusters = clustering_engine.create_clusters(eligible)

    demand_analyzer = DemandAnalyzer(exclusion_logger=exclusion_logger)
    demand_results = demand_analyzer.calculate(clusters)

    for demand in demand_results:
        demand["exclusions"] = exclusion_logger.get_records()

    return demand_results
