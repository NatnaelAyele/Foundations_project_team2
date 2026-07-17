from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.engine.coordinator import CoordinationEngine
from backend.engine.notifier import Notifier
from backend.models.operations import (
    CoordinationPlan,
    ExcludedTrip,
    ForecastAllocation,
    HarvestForecast,
    Notification,
    TripAllocation,
    TripStatusEvent,
)
from backend.models.provider import ColdHub, ColdHubCapacityUpdate, Sector, Truck
from backend.services.payment_service import PaymentService, PaymentServiceError
from sms_gateway.notifier import send_notification


class CoordinationPersistenceError(RuntimeError):
    pass


class CoordinationService:
    """Runs one sector's coordination workflow and saves its results."""

    def __init__(self, db: Session):
        self.db = db

    def run_sector(self, sector_id: int) -> dict:
        sector = self.db.get(Sector, sector_id)
        if sector is None:
            raise CoordinationPersistenceError("Sector not found")

        try:
            plan = CoordinationPlan(sector_id=sector_id, status="RUNNING")
            self.db.add(plan)
            self.db.flush()

            engine = CoordinationEngine(
                db=self.db,
                coordination_plan={"plan_id": plan.plan_id, "sector_id": sector_id},
                sector_id=sector_id,
            )
            result = engine.run()
            if result["status"] != "success":
                raise CoordinationPersistenceError(result["error"])

            reservation_count, trip_ids = self.persist_reservations(
                plan, result["reservations"]
            )
            payment_count = self.create_payment_records_for_trips(trip_ids)
            exclusion_count = self.persist_exclusions(plan, result["exclusions"])
            notification_count = self.persist_notifications(
                result["reservations"], trip_ids
            )
            plan.status = "COMPLETED"
            self.db.commit()
            self.db.refresh(plan)
            payment_initialization = self.initialize_committed_payments_for_trips(trip_ids)
            dispatch_result = self.dispatch_plan_notifications(plan.plan_id)

            return {
                "plan_id": plan.plan_id,
                "sector_id": plan.sector_id,
                "status": plan.status,
                "trip_count": reservation_count,
                "payment_count": payment_count,
                **payment_initialization,
                "exclusion_count": exclusion_count,
                "notification_count": notification_count,
                **dispatch_result,
            }
        except Exception as error:
            self.db.rollback()
            self.record_failed_plan(sector_id)
            if isinstance(error, CoordinationPersistenceError):
                raise
            raise CoordinationPersistenceError(str(error)) from error

    def persist_reservations(
        self, plan: CoordinationPlan, reservations: dict
    ) -> tuple[int, dict[str, int]]:
        forecast_allocations = reservations.get("forecast_allocations", [])
        allocations_by_trip = {}
        for forecast_allocation in forecast_allocations:
            allocations_by_trip.setdefault(
                forecast_allocation["temporary_trip_key"], []
            ).append(forecast_allocation)

        persisted_count = 0
        trip_ids = {}
        for reservation in reservations.get("trip_allocations", []):
            truck = self.lock_truck(reservation)
            hub = self.lock_hub(reservation)
            total_load = float(reservation["total_load_kg"])

            self.validate_resources(truck, hub, reservation, total_load)
            trip = TripAllocation(
                plan_id=plan.plan_id,
                truck_id=truck.truck_id,
                hub_id=hub.hub_id,
                sector_id=plan.sector_id,
                total_load_kg=total_load,
                pickup_start=reservation.get("pickup_start"),
                estimated_hub_arrival=reservation.get("estimated_hub_arrival"),
                status=reservation["database_trip_status"],
            )
            self.db.add(trip)
            self.db.flush()

            self.persist_forecast_allocations(
                trip,
                allocations_by_trip.get(reservation["temporary_trip_key"], []),
            )
            truck.status = "BUSY"
            hub.available_capacity_kg -= total_load
            self.db.add(
                ColdHubCapacityUpdate(
                    hub_id=hub.hub_id,
                    total_capacity_kg=hub.total_capacity_kg,
                    available_capacity_kg=hub.available_capacity_kg,
                    notes=f"Engine reservation for coordination plan {plan.plan_id}",
                )
            )
            self.db.add(
                TripStatusEvent(allocation_id=trip.allocation_id, status="SCHEDULED")
            )
            trip_ids[reservation["temporary_trip_key"]] = trip.allocation_id
            persisted_count += 1

        return persisted_count, trip_ids

    def create_payment_records_for_trips(self, trip_ids: dict[str, int]) -> int:
        payment_service = PaymentService(self.db)
        created = 0
        for allocation_id in trip_ids.values():
            payment_service.create_payment_record(allocation_id, auto_commit=False)
            created += 1
        return created

    def initialize_committed_payments_for_trips(self, trip_ids: dict[str, int]) -> dict:
        payment_service = PaymentService(self.db)
        initialized = 0
        failed = 0
        for allocation_id in trip_ids.values():
            try:
                payment_service.initialize_payment(allocation_id)
                initialized += 1
            except PaymentServiceError:
                self.db.rollback()
                failed += 1
        return {
            "payment_initialized_count": initialized,
            "payment_initialization_failed_count": failed,
        }

    def persist_notifications(
        self, reservations: dict, trip_ids: dict[str, int]
    ) -> int:
        notifier = Notifier()
        saved = 0
        for reservation in reservations.get("trip_allocations", []):
            trip = reservation.copy()
            trip["allocation_id"] = trip_ids[reservation["temporary_trip_key"]]
            result = notifier.create_notifications({"trip_allocations": [trip]})
            for notification in result["notifications"]:
                self.db.add(
                    Notification(
                        recipient_type=notification["recipient_type"],
                        recipient_phone=notification["recipient_phone"],
                        channel=notification["channel"],
                        message=notification["message"],
                        status="QUEUED",
                        related_trip_id=trip["allocation_id"],
                    )
                )
                saved += 1
        return saved

    def dispatch_plan_notifications(self, plan_id: int) -> dict:
        notifications = self.db.scalars(
            select(Notification)
            .join(TripAllocation, TripAllocation.allocation_id == Notification.related_trip_id)
            .where(
                TripAllocation.plan_id == plan_id,
                Notification.status == "QUEUED",
            )
            .order_by(Notification.notification_id)
        ).all()
        sent_count = 0
        failed_count = 0
        for notification in notifications:
            try:
                send_notification(
                    notification.recipient_phone,
                    notification.message,
                    notification_type=self.notification_type_for(notification),
                )
                notification.status = "SENT"
                notification.sent_time = datetime.now()
                sent_count += 1
            except Exception:
                notification.status = "FAILED"
                failed_count += 1
        self.db.commit()
        return {
            "sent_notification_count": sent_count,
            "failed_notification_count": failed_count,
        }

    def notification_type_for(self, notification: Notification) -> str:
        message = notification.message or ""
        if message.startswith("FreshLink payment initialized"):
            return "PAYMENT_INITIALIZED"
        if "payment is pending" in message:
            return "PAYMENT_PENDING"
        if "payment has been confirmed" in message:
            return "PAYMENT_SUCCESSFUL"
        if "payment failed" in message:
            return "PAYMENT_FAILED"
        if "refund" in message:
            return "PAYMENT_REFUNDED"
        return "TRIP_RESERVED"

    def persist_forecast_allocations(
        self, trip: TripAllocation, forecast_allocations: list[dict]
    ) -> None:
        if not forecast_allocations:
            raise CoordinationPersistenceError("A trip must include forecast allocations")

        for item in forecast_allocations:
            forecast = self.db.scalar(
                select(HarvestForecast)
                .where(HarvestForecast.forecast_id == item["forecast_id"])
                .with_for_update()
            )
            if forecast is None or forecast.status != "PENDING":
                raise CoordinationPersistenceError("Forecast is no longer pending")

            allocated_quantity = float(item["allocated_quantity_kg"])
            if allocated_quantity != float(forecast.quantity_kg):
                raise CoordinationPersistenceError(
                    "Partial forecast allocations are not supported"
                )

            self.db.add(
                ForecastAllocation(
                    allocation_id=trip.allocation_id,
                    forecast_id=forecast.forecast_id,
                    allocated_quantity_kg=allocated_quantity,
                )
            )
            forecast.status = "ALLOCATED"

    def persist_exclusions(self, plan: CoordinationPlan, exclusions: list[dict]) -> int:
        saved = 0
        for exclusion in exclusions:
            forecast_id = exclusion.get("forecast_id")
            if forecast_id is None:
                continue
            self.db.add(
                ExcludedTrip(
                    forecast_id=forecast_id,
                    plan_id=plan.plan_id,
                    reason_code=exclusion["reason_code"],
                    reason_detail=exclusion.get("reason_detail"),
                )
            )
            saved += 1
        return saved

    def lock_truck(self, reservation: dict) -> Truck:
        truck = self.db.scalar(
            select(Truck)
            .where(Truck.truck_id == reservation["truck_id"])
            .with_for_update()
        )
        if truck is None:
            raise CoordinationPersistenceError("Matched truck no longer exists")
        return truck

    def lock_hub(self, reservation: dict) -> ColdHub:
        hub = self.db.scalar(
            select(ColdHub)
            .where(ColdHub.hub_id == reservation["hub_id"])
            .with_for_update()
        )
        if hub is None:
            raise CoordinationPersistenceError("Matched cold hub no longer exists")
        return hub

    def validate_resources(
        self, truck: Truck, hub: ColdHub, reservation: dict, total_load: float
    ) -> None:
        if truck.status != "AVAILABLE":
            raise CoordinationPersistenceError("Matched truck is no longer available")
        if truck.sector_id != reservation["sector_id"]:
            raise CoordinationPersistenceError("Matched truck belongs to another sector")
        if truck.capacity_kg < total_load:
            raise CoordinationPersistenceError("Matched truck capacity is no longer enough")
        if hub.operating_status != "OPEN":
            raise CoordinationPersistenceError("Matched cold hub is no longer open")
        if hub.sector_id != reservation["sector_id"]:
            raise CoordinationPersistenceError("Matched cold hub belongs to another sector")
        if hub.available_capacity_kg < total_load:
            raise CoordinationPersistenceError("Matched cold hub capacity is no longer enough")

    def record_failed_plan(self, sector_id: int) -> None:
        try:
            self.db.add(CoordinationPlan(sector_id=sector_id, status="FAILED"))
            self.db.commit()
        except Exception:
            self.db.rollback()
