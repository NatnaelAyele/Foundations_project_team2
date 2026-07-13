"""
Group 1 — Prepare the data.

Implements steps 2 to 6 of the coordination engine's 12-step cycle:
    2. Read pending forecasts
    3. Validate a forecast
    4. Select eligible forecasts
    5. Cluster forecasts (by sector)
    6. Calculate demand (per cluster)

Every function here is pure and synchronous where possible: given the same
inputs, they return the same outputs. That makes them trivial to unit test
without a real database, and safe for Group 3's coordinator.py to call in
sequence.

Wiring into coordinator.py (Group 3):

    from group1_engine.pipeline import run_group1

    result = run_group1(db_session)
    # result.clusters -> feed into Group 2's truck_matcher / hub_matcher
    # result.excluded -> feed into Group 3's excluded_trips logger
"""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable

from sqlalchemy.orm import Session

from .models import HarvestForecast
from .schemas import (
    Cluster,
    ExcludedForecast,
    ForecastOut,
    Group1Result,
    ValidationError_,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Configuration — the "coordination window"
# ---------------------------------------------------------------------------
# A harvest forecast is only worth planning if its harvest_date falls inside
# a window around "now": not in the past (already spoiled / missed), and not
# so far in the future that planning it now is meaningless. Tunable in one
# place so Group 3 (or the PM) can adjust without touching validation logic.
COORDINATION_WINDOW_DAYS_AHEAD = 3


def _within_coordination_window(harvest_date: date, today: date) -> bool:
    if harvest_date < today:
        return False
    return harvest_date <= today + timedelta(days=COORDINATION_WINDOW_DAYS_AHEAD)


# ---------------------------------------------------------------------------
# Step 2 — Read pending forecasts
# ---------------------------------------------------------------------------
def read_pending_forecasts(db: Session) -> list[HarvestForecast]:
    """Query harvest_forecasts where status = 'pending', return a clean list.

    This is the only place that talks to the database in Group 1 — every
    later step works on plain Python objects, not queries.
    """
    return (
        db.query(HarvestForecast)
        .filter(HarvestForecast.status == "pending")
        .order_by(HarvestForecast.harvest_date.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# Step 3 — Validate a forecast
# ---------------------------------------------------------------------------
def validate_forecast(
    forecast: HarvestForecast, today: date | None = None
) -> ValidationResult:
    """Check one forecast is sane. Never raises — always returns a result,
    valid or not, with every reason it failed (not just the first)."""
    today = today or date.today()
    errors: list[ValidationError_] = []

    # quantity_kg must be a positive number
    try:
        qty = Decimal(str(forecast.quantity_kg))
        if qty <= 0:
            errors.append(
                ValidationError_(
                    field="quantity_kg",
                    reason="must be a positive number, got "
                    f"{forecast.quantity_kg!r}",
                )
            )
    except (InvalidOperation, TypeError, ValueError):
        errors.append(
            ValidationError_(
                field="quantity_kg",
                reason=f"is not a valid number: {forecast.quantity_kg!r}",
            )
        )

    # harvest_date must be a real date
    if not isinstance(forecast.harvest_date, date):
        errors.append(
            ValidationError_(
                field="harvest_date",
                reason=f"is not a real date: {forecast.harvest_date!r}",
            )
        )
    else:
        # harvest_date must fall inside the coordination window
        if not _within_coordination_window(forecast.harvest_date, today):
            errors.append(
                ValidationError_(
                    field="harvest_date",
                    reason=(
                        f"{forecast.harvest_date} is outside the coordination "
                        f"window ({today} .. "
                        f"{today + timedelta(days=COORDINATION_WINDOW_DAYS_AHEAD)})"
                    ),
                )
            )

    # farmer_id must exist and be linked to a real farmer
    if not forecast.farmer_id or forecast.farmer is None:
        errors.append(
            ValidationError_(
                field="farmer_id",
                reason=f"no farmer linked to farmer_id={forecast.farmer_id!r}",
            )
        )

    return ValidationResult(
        forecast_id=forecast.forecast_id,
        is_valid=len(errors) == 0,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Step 4 — Select eligible forecasts
# ---------------------------------------------------------------------------
def select_eligible(
    forecasts: Iterable[HarvestForecast], today: date | None = None
) -> tuple[list[ForecastOut], list[ExcludedForecast]]:
    """Split forecasts into (eligible, excluded).

    Eligible forecasts pass forward as clean ForecastOut objects. Excluded
    ones come back tagged with the reason code Group 3's excluded_trips
    logger expects: INVALID_FORECAST for anything except a bad date,
    OUTSIDE_WINDOW when the date itself is the only problem.
    """
    eligible: list[ForecastOut] = []
    excluded: list[ExcludedForecast] = []

    for forecast in forecasts:
        result = validate_forecast(forecast, today=today)

        if result.is_valid:
            eligible.append(
                ForecastOut(
                    forecast_id=forecast.forecast_id,
                    farmer_id=forecast.farmer_id,
                    farmer_name=(
                        forecast.farmer.full_name if forecast.farmer else None
                    ),
                    quantity_kg=float(forecast.quantity_kg),
                    harvest_date=forecast.harvest_date,
                    sector=forecast.sector,
                )
            )
            continue

        # Decide the reason code: if the *only* failing field is the date
        # (and the date really is a real date, just outside the window),
        # it's OUTSIDE_WINDOW; anything else in the mix is INVALID_FORECAST.
        only_window_issue = len(result.errors) == 1 and result.errors[
            0
        ].field == "harvest_date" and isinstance(forecast.harvest_date, date)

        reason_code = "OUTSIDE_WINDOW" if only_window_issue else "INVALID_FORECAST"
        reason_detail = "; ".join(f"{e.field}: {e.reason}" for e in result.errors)

        excluded.append(
            ExcludedForecast(
                forecast_id=forecast.forecast_id,
                reason_code=reason_code,
                reason_detail=reason_detail,
            )
        )

    return eligible, excluded


# ---------------------------------------------------------------------------
# Step 5 — Cluster forecasts (by sector)
# ---------------------------------------------------------------------------
def cluster_by_sector(eligible: list[ForecastOut]) -> dict[str, list[ForecastOut]]:
    """Group eligible forecasts by sector — same sector = same cluster.

    Returns a dict for easy lookup; use `calculate_demand` (step 6) to turn
    this into the final list-of-Cluster shape the rest of the pipeline uses.
    """
    clusters: dict[str, list[ForecastOut]] = {}
    for forecast in eligible:
        clusters.setdefault(forecast.sector, []).append(forecast)
    return clusters


# ---------------------------------------------------------------------------
# Step 6 — Calculate demand
# ---------------------------------------------------------------------------
def calculate_demand(clusters: dict[str, list[ForecastOut]]) -> list[Cluster]:
    """Sum quantity_kg per cluster, return the final Cluster objects that
    Group 2's truck_matcher / hub_matcher will consume directly."""
    result: list[Cluster] = []
    for sector, forecasts in clusters.items():
        total = sum(f.quantity_kg for f in forecasts)
        result.append(
            Cluster(sector=sector, forecasts=forecasts, total_demand_kg=total)
        )
    # Largest demand first — the matchers see the hardest-to-place clusters first.
    result.sort(key=lambda c: c.total_demand_kg, reverse=True)
    return result


# ---------------------------------------------------------------------------
# Orchestration — run all of steps 2-6 in sequence
# ---------------------------------------------------------------------------
def run_group1(db: Session, today: date | None = None) -> Group1Result:
    """Run the full Group 1 stage: read -> validate -> eligibility -> cluster
    -> demand. This is the one function Group 3's coordinator.py should call.
    """
    pending = read_pending_forecasts(db)
    eligible, excluded = select_eligible(pending, today=today)
    clusters_by_sector = cluster_by_sector(eligible)
    clusters = calculate_demand(clusters_by_sector)

    return Group1Result(
        pending_count=len(pending),
        eligible_count=len(eligible),
        excluded_count=len(excluded),
        excluded=excluded,
        clusters=clusters,
    )
