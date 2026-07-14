# Unit tests for Group 1's classes: Validator, EligibilityChecker, ClusteringEngine, DemandAnalyzer.
# Run with: pytest group1_engine/tests/test_pipeline.py -v

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from group1_engine.models import Base, Farmer, HarvestForecast, Sector
from group1_engine.pipeline import (
    Validator,
    EligibilityChecker,
    ClusteringEngine,
    DemandAnalyzer,
    read_pending_forecasts,
    run_group1_pipeline,
)

TODAY = date(2026, 7, 12)


def make_forecast(**overrides):
    defaults = dict(
        forecast_id=1,
        farmer_id=1,
        farmer_phone="0781234567",
        quantity_kg=100,
        harvest_date=datetime.combine(TODAY + timedelta(days=1), datetime.min.time()),
        sector_id=1,
    )
    defaults.update(overrides)
    return defaults


# --- Validator --------------------------------------------------------------

def test_validator_passes_a_sane_forecast():
    forecast = make_forecast()
    result = Validator(today=TODAY).validate([forecast])
    assert result == [forecast]


def test_validator_drops_non_positive_quantity():
    forecast = make_forecast(quantity_kg=-10)
    validator = Validator(today=TODAY)
    result = validator.validate([forecast])
    assert result == []
    assert validator.excluded[0]["forecast_id"] == 1


def test_validator_drops_missing_farmer():
    forecast = make_forecast(farmer_id=None)
    result = Validator(today=TODAY).validate([forecast])
    assert result == []


def test_validator_drops_missing_sector():
    forecast = make_forecast(sector_id=None)
    result = Validator(today=TODAY).validate([forecast])
    assert result == []


def test_validator_drops_bad_date():
    forecast = make_forecast(harvest_date="not-a-date")
    result = Validator(today=TODAY).validate([forecast])
    assert result == []


# --- EligibilityChecker ------------------------------------------------------

def test_eligibility_keeps_forecast_inside_window():
    forecast = make_forecast(harvest_date=datetime.combine(TODAY + timedelta(days=1), datetime.min.time()))
    result = EligibilityChecker(today=TODAY).filter([forecast])
    assert result == [forecast]


def test_eligibility_drops_forecast_outside_window():
    forecast = make_forecast(harvest_date=datetime.combine(TODAY + timedelta(days=30), datetime.min.time()))
    result = EligibilityChecker(today=TODAY).filter([forecast])
    assert result == []


def test_eligibility_drops_zero_quantity():
    forecast = make_forecast(quantity_kg=0)
    result = EligibilityChecker(today=TODAY).filter([forecast])
    assert result == []


# --- ClusteringEngine ---------------------------------------------------------

def test_clustering_groups_by_sector_and_sums_load():
    f1 = make_forecast(forecast_id=1, sector_id=1, quantity_kg=300)
    f2 = make_forecast(forecast_id=2, sector_id=1, quantity_kg=500)
    f3 = make_forecast(forecast_id=3, sector_id=2, quantity_kg=200)

    clusters = ClusteringEngine().create_clusters([f1, f2, f3])

    by_sector = {c["sector_id"]: c for c in clusters}
    assert by_sector[1]["total_load_kg"] == 800
    assert len(by_sector[1]["forecasts"]) == 2
    assert by_sector[2]["total_load_kg"] == 200


# --- DemandAnalyzer -----------------------------------------------------------

def test_demand_analyzer_returns_required_capacity_per_cluster():
    cluster = {"cluster_id": 1, "sector_id": 1, "total_load_kg": 800, "forecasts": []}
    result = DemandAnalyzer().calculate([cluster])

    assert result == [{"cluster": cluster, "required_capacity_kg": 800}]


# --- read_pending_forecasts (needs a real/fake DB) ---------------------------

@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_read_pending_forecasts_shapes_dicts_correctly(db):
    sector = Sector(sector_id=1, name="Kimironko")
    db.add(sector)
    db.commit()
    farmer = Farmer(farmer_id=1, sector_id=1, name="John Mwangi", phone="0781234567")
    db.add(farmer)
    db.commit()
    db.add(HarvestForecast(
        forecast_id=1, farmer_id=1, quantity_kg=800,
        harvest_date=datetime.combine(TODAY, datetime.min.time()), status="PENDING",
    ))
    db.add(HarvestForecast(
        forecast_id=2, farmer_id=1, quantity_kg=200,
        harvest_date=datetime.combine(TODAY, datetime.min.time()), status="CANCELLED",
    ))
    db.commit()

    forecasts = read_pending_forecasts(db)

    assert len(forecasts) == 1
    assert forecasts[0] == {
        "forecast_id": 1,
        "farmer_id": 1,
        "farmer_phone": "0781234567",
        "quantity_kg": 800.0,
        "harvest_date": datetime.combine(TODAY, datetime.min.time()),
        "sector_id": 1,
    }


# --- End-to-end ----------------------------------------------------------------

def test_run_group1_pipeline_end_to_end(db):
    sector = Sector(sector_id=1, name="Kimironko")
    db.add(sector)
    db.commit()
    farmer = Farmer(farmer_id=1, sector_id=1, name="John Mwangi", phone="0781234567")
    db.add(farmer)
    db.commit()
    db.add(HarvestForecast(
        forecast_id=1, farmer_id=1, quantity_kg=800,
        harvest_date=datetime.combine(TODAY + timedelta(days=1), datetime.min.time()), status="PENDING",
    ))
    db.add(HarvestForecast(
        forecast_id=2, farmer_id=1, quantity_kg=-5,
        harvest_date=datetime.combine(TODAY + timedelta(days=1), datetime.min.time()), status="PENDING",
    ))
    db.commit()

    result = run_group1_pipeline(db, today=TODAY)

    assert len(result) == 1
    assert result[0]["required_capacity_kg"] == 800
    assert result[0]["cluster"]["sector_id"] == 1
