from datetime import UTC, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.operations import (
    ACTIVE_TRIP_STATUSES,
    TripAllocation,
    TripStatusEvent,
)
from backend.models.provider import (
    ColdHub,
    Sector,
    Transporter,
    Truck,
    TruckOperationalDetail,
    TRUCK_STATUSES,
    User,
)
from backend.routes.accounts import require_role


router = APIRouter(prefix="/api/transporter", tags=["Transporter"])

def normalize_truck_status(value):
    if not isinstance(value, str):
        return value
    normalized = value.strip().upper().replace("-", "_")
    if normalized not in TRUCK_STATUSES:
        raise ValueError("Status must be AVAILABLE, BUSY, or MAINTENANCE")
    return normalized


class TruckCreateRequest(BaseModel):
    plate_number: str = Field(min_length=3, max_length=15)
    capacity_kg: float = Field(gt=0)
    status: Literal["AVAILABLE", "MAINTENANCE"] = "AVAILABLE"
    vehicle_model: str | None = Field(default=None, max_length=100)
    driver_name: str | None = Field(default=None, max_length=100)
    current_location: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        return normalize_truck_status(value)


class TruckUpdateRequest(BaseModel):
    plate_number: str | None = Field(default=None, min_length=3, max_length=15)
    capacity_kg: float | None = Field(default=None, gt=0)
    status: Literal["AVAILABLE", "BUSY", "MAINTENANCE"] | None = None
    vehicle_model: str | None = Field(default=None, max_length=100)
    driver_name: str | None = Field(default=None, max_length=100)
    current_location: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        return normalize_truck_status(value) if value is not None else None


def current_transporter(db: Session, user: User):
    row = db.execute(
        select(Transporter, Sector)
        .join(Sector, Sector.sector_id == Transporter.sector_id)
        .where(Transporter.user_id == user.user_id)
    ).first()
    if row is None:
        raise HTTPException(
            status_code=404, detail="No transporter is linked to this account"
        )
    return row


def owned_truck(db: Session, transporter_id: int, truck_id: int):
    truck = db.scalar(
        select(Truck).where(
            Truck.truck_id == truck_id,
            Truck.transporter_id == transporter_id,
        )
    )
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck


def truck_to_dict(truck: Truck, details: TruckOperationalDetail | None):
    return {
        "truck_id": truck.truck_id,
        "plate_number": truck.plate_number,
        "capacity_kg": truck.capacity_kg,
        "status": truck.status,
        "database_status": truck.status,
        "vehicle_model": details.vehicle_model if details else None,
        "driver_name": details.driver_name if details else None,
        "current_location": details.current_location if details else None,
        "notes": details.notes if details else None,
        "updated_at": details.updated_at if details else None,
    }


def fleet_summary(db: Session, transporter_id: int):
    trucks = db.scalars(
        select(Truck).where(Truck.transporter_id == transporter_id)
    ).all()
    available = [truck for truck in trucks if truck.status == "AVAILABLE"]
    return {
        "total_trucks": len(trucks),
        "available_trucks": len(available),
        "total_capacity_kg": sum(truck.capacity_kg for truck in trucks),
        "available_capacity_kg": sum(truck.capacity_kg for truck in available),
        "accepting_trips": bool(available),
    }


def transporter_to_dict(
    transporter: Transporter, sector: Sector, fleet: dict
):
    return {
        "transporter_id": transporter.transporter_id,
        "name": transporter.name,
        "phone": transporter.phone,
        "base_sector": sector.name,
        "district": sector.district,
        "cell": sector.cell,
        "village": sector.village,
        **fleet,
    }


@router.get("/me")
def get_transporter_profile(
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, sector = current_transporter(db, user)
    return transporter_to_dict(
        transporter, sector, fleet_summary(db, transporter.transporter_id)
    )


@router.get("/dashboard")
def get_dashboard_summary(
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, sector = current_transporter(db, user)
    fleet = fleet_summary(db, transporter.transporter_id)
    allocation_count = db.scalar(
        select(func.count(TripAllocation.allocation_id))
        .join(Truck, Truck.truck_id == TripAllocation.truck_id)
        .where(Truck.transporter_id == transporter.transporter_id)
    ) or 0
    awaiting_pickup = db.scalar(
        select(func.count(TripAllocation.allocation_id))
        .join(Truck, Truck.truck_id == TripAllocation.truck_id)
        .where(
            Truck.transporter_id == transporter.transporter_id,
            TripAllocation.status == "SCHEDULED",
        )
    ) or 0

    today = datetime.now(UTC).date()
    day_start = datetime.combine(today, time.min)
    day_end = day_start + timedelta(days=1)
    delivered_today = db.scalar(
        select(func.count(func.distinct(TripStatusEvent.allocation_id)))
        .join(
            TripAllocation,
            TripAllocation.allocation_id == TripStatusEvent.allocation_id,
        )
        .join(Truck, Truck.truck_id == TripAllocation.truck_id)
        .where(
            Truck.transporter_id == transporter.transporter_id,
            TripStatusEvent.status == "COMPLETED",
            TripStatusEvent.created_at >= day_start,
            TripStatusEvent.created_at < day_end,
        )
    ) or 0

    return {
        "transporter": transporter_to_dict(transporter, sector, fleet),
        "fleet": fleet,
        "trips": {
            "awaiting_pickup": awaiting_pickup if allocation_count else None,
            "delivered_today": delivered_today,
        },
        "coordination_data_available": allocation_count > 0,
    }


@router.get("/trucks")
def list_trucks(
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, _ = current_transporter(db, user)
    rows = db.execute(
        select(Truck, TruckOperationalDetail)
        .outerjoin(
            TruckOperationalDetail,
            TruckOperationalDetail.truck_id == Truck.truck_id,
        )
        .where(Truck.transporter_id == transporter.transporter_id)
        .order_by(Truck.plate_number)
    ).all()
    return {"items": [truck_to_dict(*row) for row in rows]}


@router.post("/trucks", status_code=status.HTTP_201_CREATED)
def create_truck(
    payload: TruckCreateRequest,
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, _ = current_transporter(db, user)
    plate_number = normalize_plate(payload.plate_number)
    if db.scalar(select(Truck).where(Truck.plate_number == plate_number)):
        raise HTTPException(status_code=409, detail="Truck plate number already exists")

    truck = Truck(
        transporter_id=transporter.transporter_id,
        plate_number=plate_number,
        capacity_kg=payload.capacity_kg,
        sector_id=transporter.sector_id,
        status=payload.status,
    )
    db.add(truck)
    db.flush()
    details = build_details(truck.truck_id, user.user_id, payload)
    if details:
        db.add(details)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Truck details already exist")
    db.refresh(truck)
    if details:
        db.refresh(details)
    return truck_to_dict(truck, details)


@router.patch("/trucks/{truck_id}")
def update_truck(
    truck_id: int,
    payload: TruckUpdateRequest,
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, _ = current_transporter(db, user)
    truck = owned_truck(db, transporter.transporter_id, truck_id)

    if payload.status is not None:
        active_trip = db.scalar(
            select(func.count(TripAllocation.allocation_id)).where(
                TripAllocation.truck_id == truck.truck_id,
                TripAllocation.status.in_(ACTIVE_TRIP_STATUSES),
            )
        ) or 0
        if payload.status == "BUSY":
            raise HTTPException(
                status_code=409,
                detail="Truck busy status is managed by trip reservations",
            )
        if active_trip:
            raise HTTPException(
                status_code=409,
                detail="A truck with an active trip cannot be changed",
            )
        truck.status = payload.status

    if payload.plate_number is not None:
        truck.plate_number = normalize_plate(payload.plate_number)
    if payload.capacity_kg is not None:
        truck.capacity_kg = payload.capacity_kg

    detail_fields = {
        "vehicle_model",
        "driver_name",
        "current_location",
        "notes",
    }
    supplied_detail_fields = detail_fields.intersection(payload.model_fields_set)
    details = db.get(TruckOperationalDetail, truck.truck_id)
    if supplied_detail_fields and details is None:
        details = TruckOperationalDetail(
            truck_id=truck.truck_id, updated_by_user_id=user.user_id
        )
        db.add(details)
    if supplied_detail_fields:
        for field_name in supplied_detail_fields:
            setattr(details, field_name, clean_optional(getattr(payload, field_name)))
        details.updated_by_user_id = user.user_id
        details.updated_at = datetime.now(UTC).replace(tzinfo=None)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Truck details conflict with another truck")
    db.refresh(truck)
    if details:
        db.refresh(details)
    return truck_to_dict(truck, details)


@router.get("/trips")
def list_trips(
    trip_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, _ = current_transporter(db, user)
    allocation_count = db.scalar(
        select(func.count(TripAllocation.allocation_id))
        .join(Truck, Truck.truck_id == TripAllocation.truck_id)
        .where(Truck.transporter_id == transporter.transporter_id)
    ) or 0
    statement = (
        select(TripAllocation, Truck, ColdHub, Sector)
        .join(Truck, Truck.truck_id == TripAllocation.truck_id)
        .join(ColdHub, ColdHub.hub_id == TripAllocation.hub_id)
        .join(Sector, Sector.sector_id == TripAllocation.sector_id)
        .where(Truck.transporter_id == transporter.transporter_id)
    )
    if trip_status:
        normalized_status = trip_status.strip().upper().replace("-", "_")
        if normalized_status in {"SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"}:
            statement = statement.where(TripAllocation.status == normalized_status)
        else:
            raise HTTPException(status_code=422, detail="Invalid trip status filter")

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.execute(
        statement
        .order_by(TripAllocation.pickup_start.desc(), TripAllocation.allocation_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [trip_to_dict(*row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "coordination_data_available": allocation_count > 0,
    }


@router.post("/trips/{allocation_id}/start")
def start_trip(
    allocation_id: int,
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, _ = current_transporter(db, user)
    allocation, truck = owned_trip(db, transporter.transporter_id, allocation_id)
    if allocation.status != "SCHEDULED":
        raise HTTPException(status_code=409, detail="This trip cannot be started")
    if truck.status != "BUSY":
        raise HTTPException(status_code=409, detail="The assigned truck is not reserved")

    allocation.status = "IN_PROGRESS"
    event = TripStatusEvent(
        allocation_id=allocation.allocation_id,
        status="IN_PROGRESS",
        changed_by_user_id=user.user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return trip_action_result(allocation, truck, event)


@router.post("/trips/{allocation_id}/deliver")
def deliver_trip(
    allocation_id: int,
    user: User = Depends(require_role("truck_provider")),
    db: Session = Depends(get_db),
):
    transporter, _ = current_transporter(db, user)
    allocation, truck = owned_trip(db, transporter.transporter_id, allocation_id)
    if allocation.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Only an in-transit trip can be delivered")

    allocation.status = "COMPLETED"
    other_active_trips = db.scalar(
        select(func.count(TripAllocation.allocation_id)).where(
            TripAllocation.truck_id == truck.truck_id,
            TripAllocation.allocation_id != allocation.allocation_id,
            TripAllocation.status.in_(ACTIVE_TRIP_STATUSES),
        )
    ) or 0
    if not other_active_trips:
        truck.status = "AVAILABLE"

    event = TripStatusEvent(
        allocation_id=allocation.allocation_id,
        status="COMPLETED",
        changed_by_user_id=user.user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    result = trip_action_result(allocation, truck, event)
    result["hub_receipt_created"] = False
    return result


def owned_trip(db: Session, transporter_id: int, allocation_id: int):
    row = db.execute(
        select(TripAllocation, Truck)
        .join(Truck, Truck.truck_id == TripAllocation.truck_id)
        .where(
            TripAllocation.allocation_id == allocation_id,
            Truck.transporter_id == transporter_id,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return row


def trip_to_dict(
    allocation: TripAllocation, truck: Truck, hub: ColdHub, sector: Sector
):
    return {
        "allocation_id": allocation.allocation_id,
        "pickup_location": {
            "sector": sector.name,
            "cell": sector.cell,
            "village": sector.village,
        },
        "pickup_start": allocation.pickup_start,
        "estimated_hub_arrival": allocation.estimated_hub_arrival,
        "total_load_kg": allocation.total_load_kg,
        "destination_hub": {"hub_id": hub.hub_id, "name": hub.name},
        "truck": {"truck_id": truck.truck_id, "plate_number": truck.plate_number},
        "status": allocation.status,
        "database_status": allocation.status,
    }


def trip_action_result(
    allocation: TripAllocation, truck: Truck, event: TripStatusEvent
):
    return {
        "ok": True,
        "allocation_id": allocation.allocation_id,
        "trip_status": allocation.status,
        "truck_status": truck.status,
        "changed_at": event.created_at,
    }


def build_details(truck_id: int, user_id: int, payload: TruckCreateRequest):
    values = {
        "vehicle_model": clean_optional(payload.vehicle_model),
        "driver_name": clean_optional(payload.driver_name),
        "current_location": clean_optional(payload.current_location),
        "notes": clean_optional(payload.notes),
    }
    if not any(values.values()):
        return None
    return TruckOperationalDetail(
        truck_id=truck_id,
        updated_by_user_id=user_id,
        **values,
    )


def normalize_plate(value: str):
    return " ".join(value.strip().upper().split())


def clean_optional(value: str | None):
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
