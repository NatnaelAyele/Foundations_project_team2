from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.config import Config
from backend.database.connection import get_db
from backend.models.provider import (
    ColdHub,
    ColdHubAccount,
    Sector,
    Transporter,
    Truck,
    User,
)


router = APIRouter(prefix="/api", tags=["Accounts"])
dashboard_router = APIRouter(tags=["Dashboards"])
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

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

    transporter_phone = db.scalar(
        select(Transporter).where(Transporter.phone == phone)
    )
    hub_phone = db.scalar(select(ColdHub).where(ColdHub.phone == phone))
    if transporter_phone or hub_phone:
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
                sector_id=sector.sector_id,
                name=registration.name.strip(),
                phone=phone,
                total_capacity_kg=registration.total_capacity_kg,
                available_capacity_kg=registration.total_capacity_kg,
            )
            db.add(provider)
            db.flush()
            db.add(ColdHubAccount(hub_id=provider.hub_id, user_id=user.user_id))
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
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    login_id = credentials.login_id.strip()
    normalized_login_id = login_id.lower()
    normalized_phone = normalize_phone(login_id)

    user = db.scalar(
        select(User)
        .outerjoin(Transporter, Transporter.user_id == User.user_id)
        .outerjoin(ColdHubAccount, ColdHubAccount.user_id == User.user_id)
        .outerjoin(ColdHub, ColdHub.hub_id == ColdHubAccount.hub_id)
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

    access_token = create_access_token(user.user_id, role)
    response.set_cookie(
        key=Config.AUTH_COOKIE_NAME,
        value=access_token,
        max_age=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=Config.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username,
        "role": role,
        "dashboard_url": DASHBOARD_URLS[role],
    }


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=Config.AUTH_COOKIE_NAME,
        path="/",
        secure=Config.COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )
    return {"message": "Logged out successfully"}


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(Config.AUTH_COOKIE_NAME)
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    payload = decode_access_token(token) if token else None
    if payload is None or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive")
    return user


def require_role(required_role):
    def check_role(user: User = Depends(get_current_user)):
        if normalize_role(user.role) != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This dashboard requires the {required_role} role",
            )
        return user

    return check_role


@dashboard_router.get("/admin/admin-dashboard.html", include_in_schema=False)
def admin_dashboard(user: User = Depends(require_role("admin"))):
    return FileResponse(FRONTEND_DIR / "admin" / "admin-dashboard.html")


@dashboard_router.get(
    "/transporter_dashboard/transporter_dashboard.html", include_in_schema=False
)
def transporter_dashboard(user: User = Depends(require_role("truck_provider"))):
    return FileResponse(
        FRONTEND_DIR / "transporter_dashboard" / "transporter_dashboard.html"
    )


@dashboard_router.get(
    "/transporter_dashboard/truck_status_update_form.html", include_in_schema=False
)
def transporter_status_page(user: User = Depends(require_role("truck_provider"))):
    return FileResponse(
        FRONTEND_DIR / "transporter_dashboard" / "truck_status_update_form.html"
    )


@dashboard_router.get(
    "/storagehub_dashboard/hub_dashboard.html", include_in_schema=False
)
def storage_hub_dashboard(user: User = Depends(require_role("hub_operator"))):
    return FileResponse(
        FRONTEND_DIR / "storagehub_dashboard" / "hub_dashboard.html"
    )


@dashboard_router.get(
    "/storagehub_dashboard/capacity_update_form.html", include_in_schema=False
)
def storage_hub_capacity_page(user: User = Depends(require_role("hub_operator"))):
    return FileResponse(
        FRONTEND_DIR / "storagehub_dashboard" / "capacity_update_form.html"
    )


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
