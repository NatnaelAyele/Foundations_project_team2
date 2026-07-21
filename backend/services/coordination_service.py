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
from backend.models.provider import ColdHub, ColdHubCapacityUpdate, Farmer, Sector, Truck
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
            payment_notifications = self.notify_payments_ready_for_trips(trip_ids)
            dispatch_result = self.dispatch_plan_notifications(plan.plan_id)
            exclusion_notifications = self.notify_exclusions(result["exclusions"])

            return {
                "plan_id": plan.plan_id,
                "sector_id": plan.sector_id,
                "status": plan.status,
                "trip_count": reservation_count,
                "payment_count": payment_count,
                **payment_notifications,
                "exclusion_count": exclusion_count,
                "notification_count": notification_count,
                **dispatch_result,
                **exclusion_notifications,
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

            self.db.flush()
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
        """
        Creates one payment PER FARMER on each trip, not one payment per
        trip. A truck typically carries several farmers' produce clustered
        together; billing only whichever farmer happened to have the
        lowest farmer_id for the whole truck's load was the original bug
        this fixes.
        """
        payment_service = PaymentService(self.db)
        created = 0
        for allocation_id in trip_ids.values():
            farmers = payment_service.get_farmers_for_allocation(allocation_id)
            for farmer in farmers:
                payment_service.create_payment_record(
                    allocation_id, farmer.farmer_id, auto_commit=False, farmer=farmer
                )
                created += 1
        return created

    def notify_payments_ready_for_trips(self, trip_ids: dict[str, int]) -> dict:
        """
        Tells EACH farmer on each trip their own payment is ready via
        USSD. This does NOT call Flutterwave or generate a hosted payment
        link - USSD farmers have no browser to open one. The actual
        Mobile Money charge only fires when a farmer presses Pay
        themselves in the USSD menu (PaymentService.initialize_momo_payment).
        """
        payment_service = PaymentService(self.db)
        notified = 0
        failed = 0
        for allocation_id in trip_ids.values():
            farmers = payment_service.get_farmers_for_allocation(allocation_id)
            for farmer in farmers:
                try:
                    payment_service.notify_payment_ready_for_ussd(allocation_id, farmer.farmer_id)
                    notified += 1
                except PaymentServiceError:
                    self.db.rollback()
                    failed += 1
        return {
            "payment_ready_notification_count": notified,
            "payment_notification_failed_count": failed,
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

                farmer_id = None
                if notification["recipient_type"] == "FARMER":
                    farmer_id = next(
                        (
                            forecast.get("farmer_id")
                            for forecast in trip.get("forecasts", [])
                            if forecast.get("farmer_phone") == notification["recipient_phone"]
                        ),
                        None,
                    )
                self.db.add(
                    Notification(
                        recipient_type=notification["recipient_type"],
                        recipient_phone=notification["recipient_phone"],
                        channel=notification["channel"],
                        message=notification["message"],
                        status="QUEUED",
                        related_trip_id=trip["allocation_id"],
                        farmer_id=farmer_id,
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
                    farmer_id=notification.farmer_id,
                    phone_number=notification.recipient_phone,
                    message=notification.message,
                    notification_type=self.notification_type_for(notification),
                )
                notification.status = "SENT"
                notification.sent_time = datetime.now()
                sent_count += 1
            except Exception as error:
                notification.status = "FAILED"
                failed_count += 1
                print(f"[dispatch_plan_notifications] send failed for "
                      f"notification {notification.notification_id}: {error}")
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

    EXCLUSION_MESSAGES = {
        "NO_TRUCK": {
            "en": "No truck is currently available in your area to collect "
                  "your tomatoes. We will try again in the next coordination "
                  "round - no action is needed from you.",
            "rw": "Nta modoka ihari ubu yo gufata inyanya zawe. Tuzongera "
                  "kugerageza vuba - nta kindi ugomba gukora.",
        },
        "NO_HUB_CAPACITY": {
            "en": "The storage facility in your area is currently full. We "
                  "will try again in the next coordination round - no "
                  "action is needed from you.",
            "rw": "Ububiko bwo mu karere kawe burimo bwuzuye ubu. Tuzongera "
                  "kugerageza vuba - nta kindi ugomba gukora.",
        },
        "NOT_ELIGIBLE": {
            "en": "Your harvest report could not be scheduled this round "
                  "because the pickup date is outside our current planning "
                  "window. Please check your report or submit a new one "
                  "with a nearer date.",
            "rw": "Raporo yawe y'umusaruro ntiyashoboye guhuzwa kubera ko "
                  "itariki iri hanze y'igihe dutegura ubu. Reba raporo "
                  "yawe cyangwa wandike indi ifite itariki iri hafi.",
        },
        "INVALID_FORECAST": {
            "en": "There was a problem with your harvest report and it "
                  "could not be scheduled. Please submit a new report or "
                  "contact support.",
            "rw": "Habaye ikibazo kuri raporo yawe y'umusaruro ntiyashoboye "
                  "guhuzwa. Wandike indi raporo cyangwa uvugane n'ubufasha.",
        },
        "INVALID_CLUSTER": {
            "en": "There was a problem scheduling your harvest report. "
                  "Please contact support if this continues.",
            "rw": "Habaye ikibazo mu guhuza raporo yawe y'umusaruro. "
                  "Vugana n'ubufasha niba bikomeje.",
        },
        "INVALID_DEMAND": {
            "en": "There was a problem scheduling your harvest report. "
                  "Please contact support if this continues.",
            "rw": "Habaye ikibazo mu guhuza raporo yawe y'umusaruro. "
                  "Vugana n'ubufasha niba bikomeje.",
        },
    }

    def notify_exclusions(self, exclusions: list[dict]) -> dict:
        """
        Sends one SMS per excluded forecast that has a farmer_id, so a
        PENDING forecast that will never be matched doesn't fail silently.
        Sent immediately (like create_payment_notification) rather than
        merely queued, since exclusions have no trip_allocation to key a
        later dispatch pass off of.
        """
        from sms_gateway.notifier import send_notification

        notified = 0
        failed = 0
        seen_forecast_ids = set()
        for exclusion in exclusions:
            farmer_id = exclusion.get("farmer_id")
            forecast_id = exclusion.get("forecast_id")
            reason_code = exclusion.get("reason_code")
            if farmer_id is None or forecast_id is None:
                continue

            if forecast_id in seen_forecast_ids:
                continue
            seen_forecast_ids.add(forecast_id)

            farmer = self.db.get(Farmer, farmer_id)
            if farmer is None:
                continue

            language = farmer.preferred_language if farmer.preferred_language in ("en", "rw") else "en"
            text = self.EXCLUSION_MESSAGES.get(reason_code, self.EXCLUSION_MESSAGES["INVALID_FORECAST"])[language]

            notification = Notification(
                recipient_type="FARMER",
                recipient_phone=farmer.phone,
                channel="SMS",
                message=text,
                status="QUEUED",
                related_trip_id=None,
                farmer_id=farmer_id,
                notification_type=f"EXCLUDED_{reason_code}",
                language=language,
            )
            self.db.add(notification)
            self.db.flush()
            try:
                send_notification(
                    farmer_id=farmer_id,
                    phone_number=farmer.phone,
                    message=text,
                    notification_type=f"EXCLUDED_{reason_code}",
                    language=language,
                )
                notification.status = "SENT"
                notification.sent_time = datetime.now()
                notified += 1
            except Exception as error:
                notification.status = "FAILED"
                failed += 1
                print(f"[notify_exclusions] send failed for forecast "
                      f"{forecast_id} ({reason_code}): {error}")
        self.db.commit()
        return {
            "exclusion_notification_count": notified,
            "exclusion_notification_failed_count": failed,
        }

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