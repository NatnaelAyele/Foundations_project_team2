# Group 1 - Prepare the data (steps 2 to 6 of the coordination engine).
# Read pending forecasts -> validate -> pick eligible ones -> cluster by sector -> sum demand.
# coordinator.py should just call run_group1(db) at the bottom of this file.

from datetime import date, datetime, timedelta
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

# I set the coordination window to "today up to 3 days ahead" - easy to change from one place.
COORDINATION_WINDOW_DAYS_AHEAD = 3


def _within_coordination_window(harvest_date: datetime, today: date) -> bool:
    # harvest_date is a full timestamp, but the window is day-based, so I only compare the date part.
    hd = harvest_date.date() if isinstance(harvest_date, datetime) else harvest_date
    if hd < today:
        return False
    return hd <= today + timedelta(days=COORDINATION_WINDOW_DAYS_AHEAD)


# Step 2 - I collect every pending harvest so I know what needs coordinating.
def read_pending_forecasts(db: Session) -> list[HarvestForecast]:
    # Status is uppercase 'PENDING' - matches what's actually in the seed data.
    return (
        db.query(HarvestForecast)
        .filter(HarvestForecast.status == "PENDING")
        .order_by(HarvestForecast.harvest_date.asc())
        .all()
    )


# Step 3 - I check each harvest is sane before I trust it.
def validate_forecast(
    forecast: HarvestForecast, today: date | None = None
) -> ValidationResult:
    # I never raise here - I collect every problem and return them all, not just the first one.
    today = today or date.today()
    errors: list[ValidationError_] = []

    # quantity_kg must be a real, positive number.
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

    # harvest_date must be an actual date/timestamp.
    if not isinstance(forecast.harvest_date, (date, datetime)):
        errors.append(
            ValidationError_(
                field="harvest_date",
                reason=f"is not a real date: {forecast.harvest_date!r}",
            )
        )
    else:
        # And it must fall inside the coordination window.
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

    # farmer_id must point to a real farmer, and that farmer needs a sector for clustering later.
    if not forecast.farmer_id or forecast.farmer is None:
        errors.append(
            ValidationError_(
                field="farmer_id",
                reason=f"no farmer linked to farmer_id={forecast.farmer_id!r}",
            )
        )
    elif forecast.farmer.sector is None:
        errors.append(
            ValidationError_(
                field="farmer_id",
                reason=f"farmer_id={forecast.farmer_id} has no linked sector",
            )
        )

    return ValidationResult(
        forecast_id=forecast.forecast_id,
        is_valid=len(errors) == 0,
        errors=errors,
    )


# Step 4 - I keep only the harvests worth planning and drop the rest.
def select_eligible(
    forecasts: Iterable[HarvestForecast], today: date | None = None
) -> tuple[list[ForecastOut], list[ExcludedForecast]]:
    eligible: list[ForecastOut] = []
    excluded: list[ExcludedForecast] = []

    for forecast in forecasts:
        result = validate_forecast(forecast, today=today)

        if result.is_valid:
            eligible.append(
                ForecastOut(
                    forecast_id=forecast.forecast_id,
                    farmer_id=forecast.farmer_id,
                    farmer_name=forecast.farmer.name if forecast.farmer else None,
                    quantity_kg=float(forecast.quantity_kg),
                    harvest_date=forecast.harvest_date,
                    sector=forecast.farmer.sector.name,
                )
            )
            continue

        # If date is the ONLY problem, I tag it OUTSIDE_WINDOW; anything else is INVALID_FORECAST.
        only_window_issue = (
            len(result.errors) == 1
            and result.errors[0].field == "harvest_date"
            and isinstance(forecast.harvest_date, (date, datetime))
        )

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


# Step 5 - I group nearby farmers so one truck can serve several at once.
def cluster_by_sector(eligible: list[ForecastOut]) -> dict[str, list[ForecastOut]]:
    # Same sector means same cluster, that's the whole rule.
    clusters: dict[str, list[ForecastOut]] = {}
    for forecast in eligible:
        clusters.setdefault(forecast.sector, []).append(forecast)
    return clusters


# Step 6 - I know exactly how many kilograms each cluster needs moved.
def calculate_demand(clusters: dict[str, list[ForecastOut]]) -> list[Cluster]:
    result: list[Cluster] = []
    for sector, forecasts in clusters.items():
        total = sum(f.quantity_kg for f in forecasts)
        result.append(
            Cluster(sector=sector, forecasts=forecasts, total_demand_kg=total)
        )
    # Biggest demand first - matchers deal with the hardest clusters to place before the easy ones.
    result.sort(key=lambda c: c.total_demand_kg, reverse=True)
    return result


# This is the one function coordinator.py should call - it runs steps 2 to 6 in order.
def run_group1(db: Session, today: date | None = None) -> Group1Result:
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
