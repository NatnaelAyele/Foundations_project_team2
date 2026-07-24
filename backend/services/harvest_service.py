from datetime import datetime, time as pytime
from sqlalchemy.orm import Session
from backend.models.operations import HarvestForecast, ForecastRequirement
from backend.models.provider import Farmer
from backend.services.coordination_service import CoordinationService, CoordinationPersistenceError
from backend.config import Config

class HarvestService:
    def __init__(self, db: Session):
        self.db = db

    def create_harvest(
        self,
        farmer_id: int,
        quantity_kg: float,
        harvest_date: datetime | str,
        harvest_time: pytime | str = pytime(8, 0),
        needs_transport: bool = True,
        needs_storage: bool = True,
        notes: str = None,
        source: str = "USSD",
        trigger_coordination: bool = True
    ) -> HarvestForecast:
        # Convert types if needed (USSD passes strings)
        if isinstance(harvest_date, str):
            harvest_date = datetime.strptime(harvest_date, "%Y-%m-%d")
        if isinstance(harvest_time, str):
            harvest_time = datetime.strptime(harvest_time, "%H:%M").time()

        # 1. Save the forecast
        forecast = HarvestForecast(
            farmer_id=farmer_id,
            quantity_kg=quantity_kg,
            harvest_date=harvest_date,
            harvest_time=harvest_time,
            status="PENDING",
        )
        self.db.add(forecast)
        self.db.flush()

        # 2. Save the requirements
        requirement = ForecastRequirement(
            forecast_id=forecast.forecast_id,
            needs_transport=needs_transport,
            needs_storage=needs_storage,
            notes=notes,
            source=source,
        )
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(forecast)

        # 3. Immediately trigger coordination if enabled.
        # The USSD gateway passes trigger_coordination=False and runs the
        # engine in a background thread instead, so the farmer's session
        # never waits on truck matching, Flutterwave, or SMS calls.
        if trigger_coordination:
            self._trigger_coordination(farmer_id)
            self.db.refresh(forecast)

        return forecast

    def update_harvest(
        self,
        forecast_id: int,
        quantity_kg: float,
        harvest_date: datetime | str,
        harvest_time: pytime | str,
        trigger_coordination: bool = True,
    ) -> HarvestForecast:
        if isinstance(harvest_date, str):
            harvest_date = datetime.strptime(harvest_date, "%Y-%m-%d")
        if isinstance(harvest_time, str):
            harvest_time = datetime.strptime(harvest_time, "%H:%M").time()

        forecast = self.db.get(HarvestForecast, forecast_id)
        if not forecast or forecast.status != "PENDING":
            raise ValueError("Forecast not found or not in PENDING status")

        forecast.quantity_kg = quantity_kg
        forecast.harvest_date = harvest_date
        forecast.harvest_time = harvest_time
        forecast.status = "PENDING"

        self.db.commit()
        self.db.refresh(forecast)

        if trigger_coordination:
            self._trigger_coordination(forecast.farmer_id)
            self.db.refresh(forecast)

        return forecast

    def _trigger_coordination(self, farmer_id: int):
        if Config.ENGINE_RUN_ON_FORECAST_CREATED:
            farmer = self.db.get(Farmer, farmer_id)
            if farmer:
                try:
                    CoordinationService(self.db).run_sector(farmer.sector_id)
                except CoordinationPersistenceError:
                    pass