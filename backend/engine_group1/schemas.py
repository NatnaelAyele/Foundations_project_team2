"""
Data shapes Group 1 hands off to everyone downstream.

Keeping these as plain Pydantic models (rather than passing raw ORM rows
around) means:
- Group 2 (truck/hub matcher) and Group 3 (planner/logger) get a stable,
  documented contract instead of having to know about SQLAlchemy internals.
- These same models serialise straight to JSON for the FastAPI demo endpoint
  and the dashboard, with zero extra glue code.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ForecastOut(BaseModel):
    """A harvest forecast, shaped for the rest of the pipeline."""

    forecast_id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    quantity_kg: float
    harvest_date: date
    sector: str

    model_config = {"from_attributes": True}


class ValidationError_(BaseModel):
    field: str
    reason: str


class ValidationResult(BaseModel):
    """Result of validating one forecast — always returned, valid or not."""

    forecast_id: int
    is_valid: bool
    errors: list[ValidationError_] = Field(default_factory=list)


class ExcludedForecast(BaseModel):
    """A forecast that did not make it to the eligible list — for Group 3's
    excluded_trips logger. reason_code matches the codes in the shared spec:
    INVALID_FORECAST or OUTSIDE_WINDOW."""

    forecast_id: int
    reason_code: str  # "INVALID_FORECAST" | "OUTSIDE_WINDOW"
    reason_detail: str


class Cluster(BaseModel):
    """All eligible forecasts for one sector, plus the total demand."""

    sector: str
    forecasts: list[ForecastOut]
    total_demand_kg: float


class Group1Result(BaseModel):
    """Everything Group 1 produces from one engine run — this is what
    Group 2's truck/hub matchers and Group 3's coordinator consume."""

    pending_count: int
    eligible_count: int
    excluded_count: int
    excluded: list[ExcludedForecast]
    clusters: list[Cluster]
