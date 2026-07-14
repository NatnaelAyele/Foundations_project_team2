from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.security import create_access_token, hash_password, verify_password
from backend.database.connection import get_db
from backend.models.provider import ColdHub, Sector, Transporter, Truck, User


router = APIRouter(prefix="/api", tags=["Accounts"])

DASHBOARD_URLS = {
    "admin": "/admin/admin-dashboard.html",
    "hub_operator": "/storagehub_dashboard/hub_dashboard.html",
    "truck_provider": "/transporter_dashboard/transporter_dashboard.html",
}


class ProviderRegistration(BaseModel):
    role: Literal["hub_operator", "truck_provider"]
    username: str = Field(min_length=4, max_length=50)
    email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=64)
    confirm_password: str
    name: str = Field(min_length=2, max_length=50)
    phone: str = Field(min_length=10, max_length=20)
    district: str = Field(min_length=2, max_length=50)
    sector: str = Field(min_length=2, max_length=50)
    cell: str = Field(min_length=2, max_length=50)
    village: str = Field(min_length=2, max_length=50)
    total_capacity_kg: float | None = Field(default=None, gt=0)
    plate_number: str | None = Field(default=None, max_length=15)
    capacity_kg: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if self.role == "hub_operator" and self.total_capacity_kg is None:
            raise ValueError("total_capacity_kg is required for a hub operator")
        if self.role == "truck_provider" and not self.plate_number:
            raise ValueError("plate_number is required for a truck provider")
        if self.role == "truck_provider" and self.capacity_kg is None:
            raise ValueError("capacity_kg is required for a truck provider")
        return self


class ProviderRegistrationResponse(BaseModel):
    message: str
    user_id: int
    role: str
    provider_id: int
    truck_id: int | None = None


class LoginRequest(BaseModel):
    login_id: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=64)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
    dashboard_url: str


@router.post(
    "/registrations/providers",
    response_model=ProviderRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_provider(registration: ProviderRegistration, db: Session = Depends(get_db)):
    username = registration.username.strip().lower()
    email = str(registration.email).lower() if registration.email else None
    phone = normalize_phone(registration.phone)

    duplicate_user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.username) == username,
                func.lower(User.email) == email if email else False,
            )
        )
    )
    if duplicate_user:
        raise HTTPException(status_code=409, detail="Username or email is already registered")

    duplicate_phone = db.scalar(
        select(User)
        .outerjoin(Transporter, Transporter.user_id == User.user_id)
        .outerjoin(ColdHub, ColdHub.user_id == User.user_id)
        .where(or_(Transporter.phone == phone, ColdHub.phone == phone))
    )
    if duplicate_phone:
        raise HTTPException(status_code=409, detail="Phone number is already registered")

    plate_number = None
    if registration.role == "truck_provider":
        plate_number = registration.plate_number.strip().upper()
        if db.scalar(select(Truck).where(Truck.plate_number == plate_number)):
            raise HTTPException(status_code=409, detail="Truck plate number is already registered")

    try:
        sector = find_or_create_sector(db, registration)
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(registration.password),
            role=registration.role,
        )
        db.add(user)
        db.flush()

        if registration.role == "hub_operator":
            provider = ColdHub(
                user_id=user.user_id,
                sector_id=sector.sector_id,
                name=registration.name.strip(),
                phone=phone,
                total_capacity_kg=registration.total_capacity_kg,
                available_capacity_kg=registration.total_capacity_kg,
            )
            db.add(provider)
            db.flush()
            provider_id = provider.hub_id
            truck_id = None
        else:
            provider = Transporter(
                user_id=user.user_id,
                sector_id=sector.sector_id,
                name=registration.name.strip(),
                phone=phone,
            )
            db.add(provider)
            db.flush()

            truck = Truck(
                transporter_id=provider.transporter_id,
                plate_number=plate_number,
                capacity_kg=registration.capacity_kg,
                sector_id=sector.sector_id,
            )
            db.add(truck)
            db.flush()
            provider_id = provider.transporter_id
            truck_id = truck.truck_id

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A provider with these details already exists")

    return {
        "message": "Provider registered successfully",
        "user_id": user.user_id,
        "role": user.role,
        "provider_id": provider_id,
        "truck_id": truck_id,
    }


@router.post("/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    login_id = credentials.login_id.strip()
    normalized_login_id = login_id.lower()
    normalized_phone = normalize_phone(login_id)

    user = db.scalar(
        select(User)
        .outerjoin(Transporter, Transporter.user_id == User.user_id)
        .outerjoin(ColdHub, ColdHub.user_id == User.user_id)
        .where(
            or_(
                func.lower(User.username) == normalized_login_id,
                func.lower(User.email) == normalized_login_id,
                Transporter.phone == normalized_phone,
                ColdHub.phone == normalized_phone,
            )
        )
    )

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive")

    role = normalize_role(user.role)
    if role not in DASHBOARD_URLS:
        raise HTTPException(status_code=403, detail="This account does not use dashboard login")

    user.last_login = datetime.now(UTC).replace(tzinfo=None)
    db.commit()

    return {
        "access_token": create_access_token(user.user_id, role),
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username,
        "role": role,
        "dashboard_url": DASHBOARD_URLS[role],
    }


def find_or_create_sector(db: Session, registration: ProviderRegistration):
    location = {
        "name": registration.sector.strip(),
        "district": registration.district.strip(),
        "cell": registration.cell.strip(),
        "village": registration.village.strip(),
    }
    sector = db.scalar(select(Sector).filter_by(**location))
    if sector:
        return sector

    sector = Sector(**location)
    db.add(sector)
    db.flush()
    return sector


def normalize_phone(phone):
    compact_phone = "".join(character for character in phone if character not in " -()")
    if compact_phone.startswith("0"):
        return "+250" + compact_phone[1:]
    if compact_phone.startswith("250"):
        return "+" + compact_phone
    return compact_phone


def normalize_role(role):
    role_aliases = {
        "admin": "admin",
        "hub_operator": "hub_operator",
        "truck_provider": "truck_provider",
        "transporter": "truck_provider",
    }
    return role_aliases.get(role.strip().lower(), role.strip().lower())
