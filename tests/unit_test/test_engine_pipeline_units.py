from datetime import date, timedelta
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.engine.exclusion_logger import ExclusionLogger
from backend.engine.hub_matcher import HubMatcher
from backend.engine.pipeline import (
    ClusteringEngine,
    DemandAnalyzer,
    EligibilityChecker,
    Validator,
)
from backend.engine.truck_matcher import TruckMatcher


TODAY = date(2026, 7, 28)


def make_forecast(**overrides):
    forecast = {
        "forecast_id": 1,
        "farmer_id": 10,
        "sector_id": 3,
        "quantity_kg": 250,
        "harvest_date": TODAY + timedelta(days=1),
    }
    forecast.update(overrides)
    return forecast


def test_validator_keeps_a_complete_forecast():
    logger = ExclusionLogger()
    valid = Validator(today=TODAY, exclusion_logger=logger).validate([make_forecast()])

    assert valid[0]["crop_type"] == "TOMATO"
    assert valid[0]["quantity"] == 250
    assert logger.get_records() == []


def test_validator_excludes_missing_farmer_and_non_positive_quantity():
    logger = ExclusionLogger()
    valid = Validator(today=TODAY, exclusion_logger=logger).validate(
        [make_forecast(farmer_id=None, quantity_kg=0)]
    )

    assert valid == []
    exclusion = logger.get_records()[0]
    assert exclusion["reason_code"] == "INVALID_FORECAST"
    assert "farmer is not registered" in exclusion["description"]
    assert "positive number" in exclusion["description"]


def test_eligibility_keeps_forecasts_inside_the_coordination_window():
    checker = EligibilityChecker(today=TODAY, window_days_ahead=3)

    eligible = checker.filter([make_forecast(harvest_date=TODAY + timedelta(days=3))])

    assert eligible == [make_forecast(harvest_date=TODAY + timedelta(days=3))]


def test_eligibility_excludes_forecasts_outside_the_coordination_window():
    logger = ExclusionLogger()
    checker = EligibilityChecker(today=TODAY, window_days_ahead=3, exclusion_logger=logger)

    eligible = checker.filter([make_forecast(harvest_date=TODAY + timedelta(days=4))])

    assert eligible == []
    assert logger.get_records()[0]["reason_code"] == "NOT_ELIGIBLE"


def test_clustering_and_demand_sum_forecast_quantity_by_sector():
    forecasts = [
        make_forecast(forecast_id=1, quantity_kg=250),
        make_forecast(forecast_id=2, quantity_kg=350),
    ]

    clusters = ClusteringEngine().create_clusters(forecasts)
    demand = DemandAnalyzer().calculate(clusters)

    assert clusters[0]["sector_id"] == 3
    assert clusters[0]["total_load_kg"] == 600
    assert demand[0]["required_capacity_kg"] == 600


def test_truck_demand_validation_rejects_an_invalid_capacity():
    matcher = TruckMatcher(db=None, truck_model=object)

    try:
        matcher.validate_demand(
            {"cluster": {"sector_id": 3}, "required_capacity_kg": 0}
        )
    except ValueError as error:
        assert "greater than zero" in str(error)
    else:
        raise AssertionError("An invalid truck demand should be rejected")


def test_hub_match_validation_rejects_missing_truck_information():
    matcher = HubMatcher(
        db=None,
        cold_hub_model=object,
        truck_model=object,
        transporter_model=object,
        user_model=object,
    )

    try:
        matcher.validate_truck_match(
            {"cluster": {"sector_id": 3, "total_load_kg": 250}}
        )
    except ValueError as error:
        assert "truck information" in str(error)
    else:
        raise AssertionError("A hub match without a truck should be rejected")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
