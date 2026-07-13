"""
Unit tests for Group 1's pipeline (steps 2-6).

Run with:  pytest group1_engine/tests/test_pipeline.py -v

Uses an in-memory SQLite DB instead of Postgres — fast, no setup, and the
SQLAlchemy models are the same either way, so this proves the logic without
needing the real database running.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from group1_engine.models import Base, Farmer, HarvestForecast
from group1_engine.pipeline import (
    calculate_demand,
    cluster_by_sector,
    read_pending_forecasts,
    select_eligible,
    validate_forecast,
    run_group1,
)

TODAY = date(2026, 7, 12)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def make_farmer(db, farmer_id=1, sector="Rugarama"):
    farmer = Farmer(
        farmer_id=farmer_id,
        full_name=f"Farmer {farmer_id}",
        phone_number=f"078000000{farmer_id}",
        sector=sector,
    )
    db.add(farmer)
    db.commit()
    return farmer


def make_forecast(db, **overrides):
    defaults = dict(
        farmer_id=1,
        quantity_kg=100,
        harvest_date=TODAY + timedelta(days=1),
        sector="Rugarama",
        status="pending",
    )
    defaults.update(overrides)
    forecast = HarvestForecast(**defaults)
    db.add(forecast)
    db.commit()
    return forecast


# --- Step 2: read_pending_forecasts -----------------------------------------

def test_read_pending_only_returns_pending_status(db):
    make_farmer(db)
    make_forecast(db, forecast_id=1, status="pending")
    make_forecast(db, forecast_id=2, status="cancelled")
    make_forecast(db, forecast_id=3, status="pending")

    pending = read_pending_forecasts(db)

    assert {f.forecast_id for f in pending} == {1, 3}


# --- Step 3: validate_forecast ----------------------------------------------

def test_validate_forecast_passes_when_all_fields_sane(db):
    make_farmer(db)
    forecast = make_forecast(db, forecast_id=1)

    result = validate_forecast(forecast, today=TODAY)

    assert result.is_valid
    assert result.errors == []


@pytest.mark.parametrize("bad_quantity", [0, -50])
def test_validate_forecast_rejects_non_positive_quantity(db, bad_quantity):
    make_farmer(db)
    forecast = make_forecast(db, forecast_id=1, quantity_kg=bad_quantity)

    result = validate_forecast(forecast, today=TODAY)

    assert not result.is_valid
    assert any(e.field == "quantity_kg" for e in result.errors)


def test_validate_forecast_rejects_past_harvest_date(db):
    make_farmer(db)
    forecast = make_forecast(
        db, forecast_id=1, harvest_date=TODAY - timedelta(days=2)
    )

    result = validate_forecast(forecast, today=TODAY)

    assert not result.is_valid
    assert any(e.field == "harvest_date" for e in result.errors)


def test_validate_forecast_rejects_date_too_far_ahead(db):
    make_farmer(db)
    forecast = make_forecast(
        db, forecast_id=1, harvest_date=TODAY + timedelta(days=30)
    )

    result = validate_forecast(forecast, today=TODAY)

    assert not result.is_valid
    assert any(e.field == "harvest_date" for e in result.errors)


def test_validate_forecast_rejects_missing_farmer(db):
    # No farmer created — farmer_id=99 points at nothing.
    forecast = HarvestForecast(
        forecast_id=1,
        farmer_id=99,
        quantity_kg=100,
        harvest_date=TODAY + timedelta(days=1),
        sector="Rugarama",
        status="pending",
    )
    db.add(forecast)
    db.commit()

    result = validate_forecast(forecast, today=TODAY)

    assert not result.is_valid
    assert any(e.field == "farmer_id" for e in result.errors)


# --- Step 4: select_eligible --------------------------------------------------

def test_select_eligible_splits_valid_and_invalid(db):
    make_farmer(db)
    make_forecast(db, forecast_id=1, quantity_kg=100)  # valid
    make_forecast(db, forecast_id=2, quantity_kg=-10)  # invalid quantity
    make_forecast(
        db, forecast_id=3, harvest_date=TODAY + timedelta(days=99)
    )  # outside window only

    forecasts = read_pending_forecasts(db)
    eligible, excluded = select_eligible(forecasts, today=TODAY)

    assert {f.forecast_id for f in eligible} == {1}
    excluded_by_id = {e.forecast_id: e for e in excluded}
    assert excluded_by_id[2].reason_code == "INVALID_FORECAST"
    assert excluded_by_id[3].reason_code == "OUTSIDE_WINDOW"


# --- Step 5 & 6: cluster_by_sector + calculate_demand ------------------------

def test_cluster_and_demand_group_and_sum_correctly(db):
    make_farmer(db, farmer_id=1, sector="Rugarama")
    make_farmer(db, farmer_id=2, sector="Rugarama")
    make_farmer(db, farmer_id=3, sector="Nyamirambo")

    make_forecast(db, forecast_id=1, farmer_id=1, sector="Rugarama", quantity_kg=200)
    make_forecast(db, forecast_id=2, farmer_id=2, sector="Rugarama", quantity_kg=150)
    make_forecast(
        db, forecast_id=3, farmer_id=3, sector="Nyamirambo", quantity_kg=80
    )

    forecasts = read_pending_forecasts(db)
    eligible, _ = select_eligible(forecasts, today=TODAY)
    clusters_by_sector = cluster_by_sector(eligible)
    clusters = calculate_demand(clusters_by_sector)

    by_sector = {c.sector: c for c in clusters}
    assert by_sector["Rugarama"].total_demand_kg == 350
    assert len(by_sector["Rugarama"].forecasts) == 2
    assert by_sector["Nyamirambo"].total_demand_kg == 80
    # Sorted largest-demand-first
    assert clusters[0].sector == "Rugarama"


# --- End-to-end: run_group1 --------------------------------------------------

def test_run_group1_end_to_end(db):
    make_farmer(db, farmer_id=1, sector="Rugarama")
    make_forecast(db, forecast_id=1, farmer_id=1, sector="Rugarama", quantity_kg=200)
    make_forecast(
        db, forecast_id=2, farmer_id=1, sector="Rugarama", quantity_kg=-5
    )  # invalid

    result = run_group1(db, today=TODAY)

    assert result.pending_count == 2
    assert result.eligible_count == 1
    assert result.excluded_count == 1
    assert len(result.clusters) == 1
    assert result.clusters[0].total_demand_kg == 200
