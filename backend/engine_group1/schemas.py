# These are the shapes I hand off to whoever uses my code next.
# Pydantic instead of raw DB rows so the matcher/coordinator don't need to know about SQLAlchemy.
# Same shapes serialise straight to JSON for api.py and the demo dashboard.

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ForecastOut(BaseModel):
    # One harvest forecast, cleaned up for the rest of the pipeline.
    forecast_id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    quantity_kg: float
    harvest_date: datetime
    sector: str

    model_config = {"from_attributes": True}


class ValidationError_(BaseModel):
    field: str
    reason: str


class ValidationResult(BaseModel):
    # What I return every time I validate one forecast - valid or not, always this, never a raised error.
    forecast_id: int
    is_valid: bool
    errors: list[ValidationError_] = Field(default_factory=list)


class ExcludedForecast(BaseModel):
    # A forecast that didn't pass validation. reason_code is INVALID_FORECAST or OUTSIDE_WINDOW.
    forecast_id: int
    reason_code: str  # "INVALID_FORECAST" | "OUTSIDE_WINDOW"
    reason_detail: str


class Cluster(BaseModel):
    # All eligible forecasts for one sector, plus the total demand.
    sector: str
    forecasts: list[ForecastOut]
    total_demand_kg: float


class Group1Result(BaseModel):
    # Everything my pipeline produces in one run.
    pending_count: int
    eligible_count: int
    excluded_count: int
    excluded: list[ExcludedForecast]
    clusters: list[Cluster]
