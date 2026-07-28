from datetime import datetime, time

from sqlalchemy import select

from backend.engine.hub_matcher import HubMatcher
from backend.engine.pipeline import run_group1_pipeline
from backend.engine.truck_matcher import TruckMatcher
from backend.models.operations import ForecastRequirement, HarvestForecast
from backend.models.provider import ColdHub, Farmer, Sector, Transporter, Truck, User


def create_forecast_data(db_session, quantity_kg=400):
    sector = Sector(name="Runda", district="Kamonyi", cell="Gacurabwenge", village="Kigusa")
    farmer_user = User(username="farmer_engine", password_hash="not-used", role="farmer")
    db_session.add_all([sector, farmer_user])
    db_session.flush()
    farmer = Farmer(
        user_id=farmer_user.user_id,
        sector_id=sector.sector_id,
        name="Engine Farmer",
        phone="+250788010001",
        cell="Gacurabwenge",
        village="Kigusa",
    )
    db_session.add(farmer)
    db_session.flush()
    forecast = HarvestForecast(
        farmer_id=farmer.farmer_id,
        quantity_kg=quantity_kg,
        harvest_date=datetime(2026, 7, 29),
        harvest_time=time(8, 0),
        status="PENDING",
    )
    db_session.add(forecast)
    db_session.flush()
    db_session.add(ForecastRequirement(forecast_id=forecast.forecast_id, needs_transport=True, needs_storage=True, source="ADMIN"))
    db_session.commit()
    return sector, farmer, forecast


def test_engine_pipeline_reads_postgresql_forecast_and_builds_demand(db_session):
    sector, _, forecast = create_forecast_data(db_session)

    demand = run_group1_pipeline(db_session, today=datetime(2026, 7, 28).date())

    assert len(demand) == 1
    assert demand[0]["sector_id"] == sector.sector_id
    assert demand[0]["required_capacity_kg"] == 400
    assert demand[0]["forecasts"][0]["forecast_id"] == forecast.forecast_id


def test_engine_records_no_truck_reason_when_no_truck_is_available(db_session):
    create_forecast_data(db_session)
    demand = run_group1_pipeline(db_session, today=datetime(2026, 7, 28).date())

    matches = TruckMatcher(db_session).match(demand)

    assert matches[0]["excluded"] is True
    assert matches[0]["reason_code"] == "NO_TRUCK"


def test_engine_matches_smallest_suitable_truck_and_hub(db_session):
    sector, _, _ = create_forecast_data(db_session)
    transporter_user = User(username="engine_transporter", password_hash="not-used", role="truck_provider")
    db_session.add(transporter_user)
    db_session.flush()
    transporter = Transporter(user_id=transporter_user.user_id, sector_id=sector.sector_id, name="Engine Transport", phone="+250788010002")
    db_session.add(transporter)
    db_session.flush()
    db_session.add_all([
        Truck(transporter_id=transporter.transporter_id, plate_number="RAA 100A", capacity_kg=500, sector_id=sector.sector_id, status="AVAILABLE"),
        Truck(transporter_id=transporter.transporter_id, plate_number="RAA 200A", capacity_kg=1000, sector_id=sector.sector_id, status="AVAILABLE"),
        ColdHub(sector_id=sector.sector_id, name="Engine Hub", phone="+250788010003", total_capacity_kg=1000, available_capacity_kg=500, operating_status="OPEN"),
    ])
    db_session.commit()

    demand = run_group1_pipeline(db_session, today=datetime(2026, 7, 28).date())
    truck_match = TruckMatcher(db_session).match(demand)
    hub_match = HubMatcher(db_session).match(truck_match)

    assert truck_match[0]["truck_capacity_kg"] == 500
    assert hub_match[0]["excluded"] is False
    assert hub_match[0]["total_load_kg"] == 400
    assert hub_match[0]["hub_capacity_kg"] == 500
