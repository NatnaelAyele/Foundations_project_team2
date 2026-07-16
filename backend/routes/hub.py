from datetime import UTC, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.operations import HubAllocationReceipt, TripAllocation
from backend.models.provider import (
    ColdHub,
    ColdHubAccount,
    ColdHubCapacityUpdate,
    Sector,
    User,
)
from backend.routes.accounts import require_role


router = APIRouter(prefix="/api/hub", tags=["Storage Hub"])


class CapacityUpdateRequest(BaseModel):
    total_capacity_kg: float = Field(gt=0)
    available_capacity_kg: float = Field(ge=0)
    produce_type: Literal["tomatoes"] = "tomatoes"
    notes: str | None = Field(default=None, max_length=500)


class ReceiptCreateRequest(BaseModel):
    received_quantity_kg: float | None = Field(default=None, gt=0)


def current_hub(db: Session, user: User):
    row = db.execute(
        select(ColdHub, Sector)
        .join(ColdHubAccount, ColdHubAccount.hub_id == ColdHub.hub_id)
        .join(Sector, Sector.sector_id == ColdHub.sector_id)
        .where(ColdHubAccount.user_id == user.user_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="No cold hub is linked to this account")
    return row


def hub_to_dict(hub: ColdHub, sector: Sector):
    available_percentage = 0
    if hub.total_capacity_kg > 0:
        available_percentage = round(
            hub.available_capacity_kg / hub.total_capacity_kg * 100, 1
        )
    return {
        "hub_id": hub.hub_id,
        "name": hub.name,
        "phone": hub.phone,
        "district": sector.district,
        "sector": sector.name,
        "cell": sector.cell,
        "village": sector.village,
        "total_capacity_kg": hub.total_capacity_kg,
        "available_capacity_kg": hub.available_capacity_kg,
        "available_percentage": available_percentage,
        "operating_status": hub.operating_status,
        "accepting_deliveries": hub.operating_status.upper() == "OPEN",
        "produce_type": "tomatoes",
    }


def latest_capacity_update(db: Session, hub_id: int):
    return db.scalar(
        select(ColdHubCapacityUpdate)
        .where(ColdHubCapacityUpdate.hub_id == hub_id)
        .order_by(
            ColdHubCapacityUpdate.created_at.desc(),
            ColdHubCapacityUpdate.update_id.desc(),
        )
        .limit(1)
    )


@router.get("/me")
def get_hub_profile(
    user: User = Depends(require_role("hub_operator")),
    db: Session = Depends(get_db),
):
    hub, sector = current_hub(db, user)
    return hub_to_dict(hub, sector)


@router.get("/capacity")
def get_capacity(
    user: User = Depends(require_role("hub_operator")),
    db: Session = Depends(get_db),
):
    hub, sector = current_hub(db, user)
    last_update = latest_capacity_update(db, hub.hub_id)
    return {
        **hub_to_dict(hub, sector),
        "notes": last_update.notes if last_update else None,
        "last_updated_at": last_update.created_at if last_update else None,
    }


@router.patch("/capacity")
def update_capacity(
    payload: CapacityUpdateRequest,
    user: User = Depends(require_role("hub_operator")),
    db: Session = Depends(get_db),
):
    if payload.available_capacity_kg > payload.total_capacity_kg:
        raise HTTPException(
            status_code=422,
            detail="Available capacity cannot exceed total capacity",
        )

    hub, sector = current_hub(db, user)
    hub.total_capacity_kg = payload.total_capacity_kg
    hub.available_capacity_kg = payload.available_capacity_kg

    update = ColdHubCapacityUpdate(
        hub_id=hub.hub_id,
        updated_by_user_id=user.user_id,
        total_capacity_kg=payload.total_capacity_kg,
        available_capacity_kg=payload.available_capacity_kg,
        produce_type=payload.produce_type,
        notes=clean_optional(payload.notes),
    )
    db.add(update)
    db.commit()
    db.refresh(update)

    return {
        **hub_to_dict(hub, sector),
        "notes": update.notes,
        "last_updated_at": update.created_at,
    }


@router.get("/dashboard")
def dashboard_summary(
    user: User = Depends(require_role("hub_operator")),
    db: Session = Depends(get_db),
):
    hub, sector = current_hub(db, user)
    allocation_count = db.scalar(
        select(func.count(TripAllocation.allocation_id)).where(
            TripAllocation.hub_id == hub.hub_id
        )
    ) or 0
    pending_count = db.scalar(
        select(func.count(TripAllocation.allocation_id))
        .outerjoin(
            HubAllocationReceipt,
            HubAllocationReceipt.allocation_id == TripAllocation.allocation_id,
        )
        .where(
            TripAllocation.hub_id == hub.hub_id,
            HubAllocationReceipt.allocation_id.is_(None),
        )
    ) or 0

    today = datetime.now(UTC).date()
    day_start = datetime.combine(today, time.min)
    day_end = day_start + timedelta(days=1)
    confirmed_today = db.scalar(
        select(func.count(HubAllocationReceipt.allocation_id))
        .join(
            TripAllocation,
            TripAllocation.allocation_id == HubAllocationReceipt.allocation_id,
        )
        .where(
            TripAllocation.hub_id == hub.hub_id,
            HubAllocationReceipt.confirmed_at >= day_start,
            HubAllocationReceipt.confirmed_at < day_end,
        )
    ) or 0

    return {
        "hub": hub_to_dict(hub, sector),
        "statistics": {
            "pending_allocations": pending_count if allocation_count else None,
            "confirmed_today": confirmed_today,
        },
        "coordination_data_available": allocation_count > 0,
    }


@router.get("/allocations")
def list_allocations(
    receipt_status: Literal["PENDING", "CONFIRMED"] | None = Query(
        default=None, alias="status"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_role("hub_operator")),
    db: Session = Depends(get_db),
):
    hub, _ = current_hub(db, user)
    statement = (
        select(TripAllocation, HubAllocationReceipt)
        .outerjoin(
            HubAllocationReceipt,
            HubAllocationReceipt.allocation_id == TripAllocation.allocation_id,
        )
        .where(TripAllocation.hub_id == hub.hub_id)
    )
    if receipt_status == "PENDING":
        statement = statement.where(HubAllocationReceipt.allocation_id.is_(None))
    elif receipt_status == "CONFIRMED":
        statement = statement.where(HubAllocationReceipt.allocation_id.is_not(None))

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.execute(
        statement
        .order_by(TripAllocation.pickup_start.desc(), TripAllocation.allocation_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    for allocation, receipt in rows:
        items.append(
            {
                "allocation_id": allocation.allocation_id,
                "farmer": None,
                "quantity_kg": None,
                "total_load_kg": allocation.total_load_kg,
                "pickup_start": allocation.pickup_start,
                "estimated_hub_arrival": allocation.estimated_hub_arrival,
                "engine_status": allocation.status,
                "receipt_status": "CONFIRMED" if receipt else "PENDING",
                "confirmed_at": receipt.confirmed_at if receipt else None,
                "received_quantity_kg": (
                    receipt.received_quantity_kg if receipt else None
                ),
                "farmer_data_available": False,
            }
        )

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "coordination_data_available": total > 0,
        "farmer_data_available": False,
    }


@router.post("/allocations/{allocation_id}/confirm")
def confirm_allocation_received(
    allocation_id: int,
    payload: ReceiptCreateRequest | None = None,
    user: User = Depends(require_role("hub_operator")),
    db: Session = Depends(get_db),
):
    hub, _ = current_hub(db, user)
    allocation = db.scalar(
        select(TripAllocation).where(
            TripAllocation.allocation_id == allocation_id,
            TripAllocation.hub_id == hub.hub_id,
        )
    )
    if allocation is None:
        raise HTTPException(status_code=404, detail="Allocation not found")

    existing = db.get(HubAllocationReceipt, allocation_id)
    if existing:
        return receipt_to_dict(existing, created=False)

    quantity = (
        payload.received_quantity_kg
        if payload and payload.received_quantity_kg is not None
        else allocation.total_load_kg
    )
    receipt = HubAllocationReceipt(
        allocation_id=allocation.allocation_id,
        confirmed_by_user_id=user.user_id,
        received_quantity_kg=quantity,
    )
    db.add(receipt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.get(HubAllocationReceipt, allocation_id)
        if existing:
            return receipt_to_dict(existing, created=False)
        raise
    db.refresh(receipt)
    return receipt_to_dict(receipt, created=True)


def receipt_to_dict(receipt: HubAllocationReceipt, created: bool):
    return {
        "ok": True,
        "created": created,
        "allocation_id": receipt.allocation_id,
        "receipt_status": "CONFIRMED",
        "confirmed_at": receipt.confirmed_at,
        "received_quantity_kg": receipt.received_quantity_kg,
        "capacity_adjusted": False,
    }


def clean_optional(value: str | None):
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
