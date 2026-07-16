import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import or_, select

from backend.config import Config
from backend.database.connection import SessionLocal
from backend.engine.logger import EngineLogger
from backend.models.operations import ForecastRequirement, HarvestForecast
from backend.models.provider import Farmer
from backend.services.coordination_service import (
    CoordinationPersistenceError,
    CoordinationService,
)


class CoordinationScheduler:
    """Runs pending sector coordination every configured interval."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.logger = EngineLogger()
        self.run_lock = threading.Lock()
        self.scheduler = BackgroundScheduler(daemon=True)
        self.scheduler.add_job(
            self.run_pending_sectors,
            trigger=IntervalTrigger(hours=Config.ENGINE_RUN_INTERVAL_HOURS),
            id="freshlink_coordination",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

    def start(self):
        self.scheduler.start()
        self.logger.info(
            f"Coordination scheduler started with a "
            f"{Config.ENGINE_RUN_INTERVAL_HOURS}-hour interval."
        )

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def run_pending_sectors(self):
        if not self.run_lock.acquire(blocking=False):
            self.logger.warning("Coordination scheduler skipped an overlapping run.")
            return []

        db = self.session_factory()
        try:
            sector_ids = db.scalars(
                select(Farmer.sector_id)
                .join(
                    HarvestForecast,
                    HarvestForecast.farmer_id == Farmer.farmer_id,
                )
                .outerjoin(
                    ForecastRequirement,
                    ForecastRequirement.forecast_id == HarvestForecast.forecast_id,
                )
                .where(
                    HarvestForecast.status == "PENDING",
                    or_(
                        ForecastRequirement.forecast_id.is_(None),
                        ForecastRequirement.needs_transport.is_(True),
                    ),
                    or_(
                        ForecastRequirement.forecast_id.is_(None),
                        ForecastRequirement.needs_storage.is_(True),
                    ),
                )
                .distinct()
                .order_by(Farmer.sector_id)
            ).all()

            results = []
            for sector_id in sector_ids:
                try:
                    results.append(CoordinationService(db).run_sector(sector_id))
                except CoordinationPersistenceError as error:
                    self.logger.error(
                        f"Coordination failed for sector {sector_id}: {error}"
                    )
            return results
        finally:
            db.close()
            self.run_lock.release()
