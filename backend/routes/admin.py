import secrets
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.security import hash_password
from backend.database.connection import get_db
from backend.models.operations import (
    CoordinationPlan,
    ExcludedTrip,
    ForecastRequirement,
    HarvestForecast,
    TripAllocation,
)
from backend.models.provider import Farmer, FarmerAdminProfile, Sector, User
from backend.routes.accounts import require_role


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))],
)


class FarmerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=20)
    national_id: str | None = Field(default=None, max_length=20)
    district: str = Field(default="Kamonyi", min_length=2, max_length=50)
    sector: str = Field(min_length=2, max_length=50)
    cell: str = Field(min_length=2, max_length=50)
    village: str = Field(min_length=2, max_length=50)
    status: Literal["ACTIVE", "PENDING_REVIEW", "INACTIVE"] = "ACTIVE"


class ForecastCreate(BaseModel):
    farmer_id: int = Field(gt=0)
    quantity_kg: float = Field(gt=0)
    harvest_date: date
    needs_transport: bool
    needs_storage: bool
    notes: str | None = Field(default=None, max_length=500)


@router.get("/sectors")
def list_sectors(district: str = "Kamonyi", db: Session = Depends(get_db)):
    rows = db.execute(
        select(Sector.name, Sector.district)
        .where(func.lower(Sector.district) == district.strip().lower())
        .distinct()
        .order_by(Sector.name)
    ).all()
    return {"items": [{"name": row.name, "district": row.district} for row in rows]}


@router.post("/farmers", status_code=status.HTTP_201_CREATED)
def create_farmer(payload: FarmerCreate, db: Session = Depends(get_db)):
    phone = normalize_farmer_phone(payload.phone)
    national_id = clean_optional(payload.national_id)

    if db.scalar(select(Farmer).where(Farmer.phone == phone)):
        raise HTTPException(status_code=409, detail="Phone number is already registered")
    if national_id and db.scalar(
        select(FarmerAdminProfile).where(
            FarmerAdminProfile.national_id == national_id
        )
    ):
        raise HTTPException(status_code=409, detail="National ID is already registered")

    try:
        sector = find_or_create_location(db, payload)
        user = User(
            username="farmer_" + phone[1:],
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role="farmer",
            is_active=payload.status != "INACTIVE",
        )
        db.add(user)
        db.flush()

        farmer = Farmer(
            user_id=user.user_id,
            sector_id=sector.sector_id,
            name=payload.name.strip(),
            phone=phone,
            cell=payload.cell.strip(),
            village=payload.village.strip(),
        )
        db.add(farmer)
        db.flush()

        profile = FarmerAdminProfile(
            farmer_id=farmer.farmer_id,
            national_id=national_id,
            registration_status=payload.status,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Farmer details already exist")

    return farmer_to_dict(farmer, sector, profile, user.created_at)


@router.get("/farmers")
def list_farmers(
    search: str | None = None,
    sector: str | None = None,
    farmer_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = farmer_select()
    conditions = []
    if search:
        value = f"%{search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Farmer.name).like(value),
                func.lower(Sector.name).like(value),
                func.lower(Farmer.village).like(value),
                Farmer.phone.like(f"%{search.strip()}%"),
            )
        )
    if sector:
        conditions.append(func.lower(Sector.name) == sector.strip().lower())
    if farmer_status:
        conditions.append(
            func.coalesce(FarmerAdminProfile.registration_status, "ACTIVE")
            == farmer_status.strip().upper()
        )

    if conditions:
        statement = statement.where(*conditions)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = db.scalar(count_statement) or 0
    rows = db.execute(
        statement
        .order_by(
            func.coalesce(FarmerAdminProfile.registered_at, User.created_at).desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "items": [farmer_to_dict(*row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post("/forecasts", status_code=status.HTTP_201_CREATED)
def create_forecast(payload: ForecastCreate, db: Session = Depends(get_db)):
    farmer = db.get(Farmer, payload.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")

    forecast = HarvestForecast(
        farmer_id=farmer.farmer_id,
        quantity_kg=payload.quantity_kg,
        harvest_date=datetime.combine(payload.harvest_date, time.min),
        status="PENDING",
    )
    db.add(forecast)
    db.flush()

    requirement = ForecastRequirement(
        forecast_id=forecast.forecast_id,
        needs_transport=payload.needs_transport,
        needs_storage=payload.needs_storage,
        notes=clean_optional(payload.notes),
        source="ADMIN",
    )
    db.add(requirement)
    db.commit()
    db.refresh(forecast)

    sector = db.get(Sector, farmer.sector_id)
    return forecast_to_dict(forecast, farmer, sector, requirement)


@router.get("/forecasts")
def list_forecasts(
    search: str | None = None,
    sector: str | None = None,
    forecast_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = forecast_select()
    conditions = []
    if search:
        value = f"%{search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Farmer.name).like(value),
                func.lower(Sector.name).like(value),
                func.lower(HarvestForecast.status).like(value),
            )
        )
    if sector:
        conditions.append(func.lower(Sector.name) == sector.strip().lower())
    if forecast_status:
        conditions.append(
            func.upper(HarvestForecast.status) == forecast_status.strip().upper()
        )
    if conditions:
        statement = statement.where(*conditions)

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.execute(
        statement
        .order_by(HarvestForecast.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [forecast_to_dict(*row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    week_start = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)
    farmer_total = db.scalar(select(func.count(Farmer.farmer_id))) or 0
    farmers_this_week = db.scalar(
        select(func.count(Farmer.farmer_id))
        .join(User, User.user_id == Farmer.user_id)
        .outerjoin(
            FarmerAdminProfile, FarmerAdminProfile.farmer_id == Farmer.farmer_id
        )
        .where(
            func.coalesce(FarmerAdminProfile.registered_at, User.created_at)
            >= week_start
        )
    ) or 0

    forecast_total = db.scalar(select(func.count(HarvestForecast.forecast_id))) or 0
    forecasts_this_week = db.scalar(
        select(func.count(HarvestForecast.forecast_id)).where(
            HarvestForecast.submitted_at >= week_start
        )
    ) or 0
    needing_transport = pending_requirement_count(db, "needs_transport")
    needing_storage = pending_requirement_count(db, "needs_storage")

    recent_farmers = db.execute(
        farmer_select()
        .order_by(
            func.coalesce(FarmerAdminProfile.registered_at, User.created_at).desc()
        )
        .limit(4)
    ).all()
    recent_forecasts = db.execute(
        forecast_select().order_by(HarvestForecast.submitted_at.desc()).limit(4)
    ).all()

    return {
        "farmers": {
            "total": farmer_total,
            "registered_this_week": farmers_this_week,
        },
        "forecasts": {
            "total": forecast_total,
            "submitted_this_week": forecasts_this_week,
            "needing_transport": needing_transport,
            "needing_storage": needing_storage,
        },
        "recent_farmers": [farmer_to_dict(*row) for row in recent_farmers],
        "recent_forecasts": [forecast_to_dict(*row) for row in recent_forecasts],
        "engine": {
            "available": False,
            "message": "Engine health integration is not implemented yet",
        },
    }


@router.get("/reports")
def admin_reports(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    today = datetime.now(UTC).date()
    start_date = date_from or today.replace(day=1)
    end_date = date_to or today
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="date_to must be on or after date_from")

    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min)
    forecast_period = (
        HarvestForecast.harvest_date >= start_at,
        HarvestForecast.harvest_date < end_at,
    )

    total_harvest = db.scalar(
        select(func.coalesce(func.sum(HarvestForecast.quantity_kg), 0)).where(
            *forecast_period
        )
    )
    sector_rows = db.execute(
        select(Sector.name, func.sum(HarvestForecast.quantity_kg).label("quantity_kg"))
        .join(Farmer, Farmer.sector_id == Sector.sector_id)
        .join(HarvestForecast, HarvestForecast.farmer_id == Farmer.farmer_id)
        .where(*forecast_period)
        .group_by(Sector.name)
        .order_by(func.sum(HarvestForecast.quantity_kg).desc())
    ).all()

    plan_period = (
        CoordinationPlan.generated_at >= start_at,
        CoordinationPlan.generated_at < end_at,
    )
    plan_count = db.scalar(
        select(func.count(CoordinationPlan.plan_id)).where(*plan_period)
    ) or 0
    coordination_available = plan_count > 0

    trips_coordinated = None
    excluded_unmatched = None
    exclusion_reasons = []
    if coordination_available:
        trips_coordinated = db.scalar(
            select(func.count(TripAllocation.allocation_id))
            .join(
                CoordinationPlan,
                CoordinationPlan.plan_id == TripAllocation.plan_id,
            )
            .where(*plan_period)
        ) or 0
        excluded_unmatched = db.scalar(
            select(func.count(ExcludedTrip.exclusion_id))
            .join(
                CoordinationPlan,
                CoordinationPlan.plan_id == ExcludedTrip.plan_id,
            )
            .where(*plan_period)
        ) or 0
        reason_rows = db.execute(
            select(ExcludedTrip.reason_code, func.count(ExcludedTrip.exclusion_id))
            .join(
                CoordinationPlan,
                CoordinationPlan.plan_id == ExcludedTrip.plan_id,
            )
            .where(*plan_period)
            .group_by(ExcludedTrip.reason_code)
            .order_by(func.count(ExcludedTrip.exclusion_id).desc())
        ).all()
        exclusion_reasons = [
            {"reason": row[0], "count": row[1]} for row in reason_rows
        ]

    return {
        "period": {"from": start_date, "to": end_date},
        "total_harvest_kg": float(total_harvest),
        "harvest_by_sector": [
            {"sector": row.name, "quantity_kg": float(row.quantity_kg)}
            for row in sector_rows
        ],
        "coordination_data_available": coordination_available,
        "trips_coordinated": trips_coordinated,
        "excluded_unmatched": excluded_unmatched,
        "exclusion_reasons": exclusion_reasons,
        "successfully_matched_percent": None,
        "matching_blocker": (
            "A forecast-to-allocation relationship is required to calculate matching"
        ),
    }


def farmer_select():
    return (
        select(Farmer, Sector, FarmerAdminProfile, User.created_at)
        .join(Sector, Sector.sector_id == Farmer.sector_id)
        .join(User, User.user_id == Farmer.user_id)
        .outerjoin(
            FarmerAdminProfile, FarmerAdminProfile.farmer_id == Farmer.farmer_id
        )
    )


def forecast_select():
    return (
        select(HarvestForecast, Farmer, Sector, ForecastRequirement)
        .join(Farmer, Farmer.farmer_id == HarvestForecast.farmer_id)
        .join(Sector, Sector.sector_id == Farmer.sector_id)
        .outerjoin(
            ForecastRequirement,
            ForecastRequirement.forecast_id == HarvestForecast.forecast_id,
        )
    )


def pending_requirement_count(db: Session, field_name):
    requirement_field = getattr(ForecastRequirement, field_name)
    return db.scalar(
        select(func.count(HarvestForecast.forecast_id))
        .outerjoin(
            ForecastRequirement,
            ForecastRequirement.forecast_id == HarvestForecast.forecast_id,
        )
        .where(
            func.upper(HarvestForecast.status) == "PENDING",
            func.coalesce(requirement_field, True).is_(True),
        )
    ) or 0


def farmer_to_dict(farmer, sector, profile, fallback_created_at):
    return {
        "farmer_id": farmer.farmer_id,
        "name": farmer.name,
        "phone": international_phone(farmer.phone),
        "national_id": profile.national_id if profile else None,
        "district": sector.district,
        "sector": sector.name,
        "cell": farmer.cell,
        "village": farmer.village,
        "status": profile.registration_status if profile else "ACTIVE",
        "registered_at": profile.registered_at if profile else fallback_created_at,
    }


def forecast_to_dict(forecast, farmer, sector, requirement):
    return {
        "forecast_id": forecast.forecast_id,
        "farmer_id": farmer.farmer_id,
        "farmer_name": farmer.name,
        "sector": sector.name,
        "quantity_kg": forecast.quantity_kg,
        "harvest_date": forecast.harvest_date,
        "status": forecast.status,
        "needs_transport": requirement.needs_transport if requirement else True,
        "needs_storage": requirement.needs_storage if requirement else True,
        "notes": requirement.notes if requirement else None,
        "source": requirement.source if requirement else "USSD",
        "submitted_at": forecast.submitted_at,
    }


def find_or_create_location(db: Session, payload: FarmerCreate):
    location = {
        "name": payload.sector.strip(),
        "district": payload.district.strip(),
        "cell": payload.cell.strip(),
        "village": payload.village.strip(),
    }
    sector = db.scalar(select(Sector).filter_by(**location))
    if sector:
        return sector
    sector = Sector(**location)
    db.add(sector)
    db.flush()
    return sector


def normalize_farmer_phone(phone):
    compact = "".join(character for character in phone if character not in " -()")
    if compact.startswith("+250"):
        compact = "0" + compact[4:]
    elif compact.startswith("250"):
        compact = "0" + compact[3:]
    if len(compact) != 10 or not compact.startswith("07") or not compact.isdigit():
        raise HTTPException(status_code=422, detail="Enter a valid Rwanda phone number")
    return compact


def international_phone(phone):
    return "+250" + phone[1:] if phone.startswith("0") else phone


def clean_optional(value):
    return value.strip() if value and value.strip() else None
