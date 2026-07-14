
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from .models import HarvestForecast

# Coordination window - how far ahead a harvest date can be and still get planned.
COORDINATION_WINDOW_DAYS_AHEAD = 3


# Step 2 - not a class in Group 3's guide, just the read that feeds everything else.
# Converts ORM rows into the plain dict shape the classes below (and Group 2/3) expect.
def read_pending_forecasts(db: Session) -> list[dict]:
    rows = (
        db.query(HarvestForecast)
        .filter(HarvestForecast.status == "PENDING")
        .order_by(HarvestForecast.harvest_date.asc())
        .all()
    )
    forecasts = []
    for r in rows:
        forecasts.append({
            "forecast_id": r.forecast_id,
            "farmer_id": r.farmer_id,
            "farmer_phone": r.farmer.phone if r.farmer else None,
            "quantity_kg": float(r.quantity_kg) if r.quantity_kg is not None else r.quantity_kg,
            "harvest_date": r.harvest_date,
            "sector_id": r.farmer.sector_id if r.farmer else None,
        })
    return forecasts


class Validator:
    # Step 3 - checks whether the info the farmer entered is correct.
    # validate(forecasts) -> only the forecasts that are valid, per the guide's exact spec.

    def __init__(self, today: date | None = None):
        self.today = today or date.today()
        # Not part of Group 3's required interface, but I keep the reasons here in
        # case the exclusion logger (Group 3) wants them later - nothing gets thrown away.
        self.excluded = []

    def validate(self, forecasts: list[dict]) -> list[dict]:
        valid = []
        self.excluded = []
        for f in forecasts:
            reasons = self._check(f)
            if reasons:
                self.excluded.append({"forecast_id": f.get("forecast_id"), "reasons": reasons})
            else:
                valid.append(f)
        return valid

    def _check(self, f: dict) -> list[str]:
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
    # Step 4 - not every valid forecast should be transported immediately.
    # filter(forecasts) -> only the forecasts that are actually ready.

    def __init__(self, today: date | None = None, window_days_ahead: int = COORDINATION_WINDOW_DAYS_AHEAD):
        self.today = today or date.today()
        self.window_days_ahead = window_days_ahead

    def filter(self, forecasts: list[dict]) -> list[dict]:
        return [f for f in forecasts if self._is_ready(f)]

    def _is_ready(self, f: dict) -> bool:
        hd = f.get("harvest_date")
        if not isinstance(hd, (date, datetime)):
            return False
        hd_date = hd.date() if isinstance(hd, datetime) else hd

        # Harvest date must fall inside the coordination window (not past, not too far ahead).
        within_window = self.today <= hd_date <= self.today + timedelta(days=self.window_days_ahead)

        # Quantity must actually be enough to be worth sending a truck for.
        quantity = f.get("quantity_kg") or 0
        has_quantity = quantity > 0

        return within_window and has_quantity


class ClusteringEngine:
    # Step 5 - groups nearby farmers so one truck can serve several at once.
    # create_clusters(forecasts) -> list of clusters, same sector = same cluster.

    def create_clusters(self, forecasts: list[dict]) -> list[dict]:
        buckets: dict = {}
        for f in forecasts:
            sector_id = f.get("sector_id")
            buckets.setdefault(sector_id, []).append(f)

        clusters = []
        for cluster_id, (sector_id, flist) in enumerate(buckets.items(), start=1):
            total_load_kg = sum(f.get("quantity_kg", 0) for f in flist)
            clusters.append({
                "cluster_id": cluster_id,
                "sector_id": sector_id,
                "total_load_kg": total_load_kg,
                "forecasts": flist,
            })
        return clusters


class DemandAnalyzer:
    # Step 6 - now that farmers are grouped, work out how much transport each cluster needs.
    # calculate(clusters) -> demand info per cluster, this is what Group 2's TruckMatcher reads.

    def calculate(self, clusters: list[dict]) -> list[dict]:
        return [
            {"cluster": cluster, "required_capacity_kg": cluster["total_load_kg"]}
            for cluster in clusters
        ]


# Convenience wrapper chaining my 4 classes together - not part of Group 3's required interface,
# just makes it easy to run all of Group 1's steps in one call for my own testing/demo.
def run_group1_pipeline(db: Session, today: date | None = None) -> list[dict]:
    forecasts = read_pending_forecasts(db)

    validator = Validator(today=today)
    valid = validator.validate(forecasts)

    eligibility_checker = EligibilityChecker(today=today)
    eligible = eligibility_checker.filter(valid)

    clustering_engine = ClusteringEngine()
    clusters = clustering_engine.create_clusters(eligible)

    demand_analyzer = DemandAnalyzer()
    return demand_analyzer.calculate(clusters)
