from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.security import hash_password
from backend.models.provider import ColdHub, Sector, Transporter, Truck, User


def register_provider(db: Session, registration):
    duplicate_user = db.scalar(
        select(User).where(
            or_(
                User.username == registration.username,
                User.email == registration.email if registration.email else False,
            )
        )
    )
    if duplicate_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )

    if registration.role == "truck_provider":
        plate_number = registration.plate_number.strip().upper()
        if db.scalar(select(Truck).where(Truck.plate_number == plate_number)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Truck plate number is already registered",
            )

    try:
        sector = find_or_create_sector(db, registration)
        user = User(
            username=registration.username.strip(),
            email=str(registration.email).lower() if registration.email else None,
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
                phone=registration.phone.strip(),
                total_capacity_kg=registration.total_capacity_kg,
                available_capacity_kg=registration.total_capacity_kg,
            )
            db.add(provider)
            db.flush()
            truck_id = None
        else:
            provider = Transporter(
                user_id=user.user_id,
                sector_id=sector.sector_id,
                name=registration.name.strip(),
                phone=registration.phone.strip(),
            )
            db.add(provider)
            db.flush()

            truck = Truck(
                transporter_id=provider.transporter_id,
                plate_number=registration.plate_number.strip().upper(),
                capacity_kg=registration.capacity_kg,
                sector_id=sector.sector_id,
            )
            db.add(truck)
            db.flush()
            truck_id = truck.truck_id

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A provider with these details already exists",
        )

    provider_id = provider.hub_id if registration.role == "hub_operator" else provider.transporter_id
    return {
        "message": "Provider registered successfully",
        "user_id": user.user_id,
        "role": user.role,
        "provider_id": provider_id,
        "truck_id": truck_id,
    }


def find_or_create_sector(db: Session, registration):
    sector = db.scalar(
        select(Sector).where(
            Sector.name == registration.sector.strip(),
            Sector.district == registration.district.strip(),
            Sector.cell == registration.cell.strip(),
            Sector.village == registration.village.strip(),
        )
    )
    if sector:
        return sector

    sector = Sector(
        name=registration.sector.strip(),
        district=registration.district.strip(),
        cell=registration.cell.strip(),
        village=registration.village.strip(),
    )
    db.add(sector)
    db.flush()
    return sector
