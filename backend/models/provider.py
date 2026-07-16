from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


TRUCK_STATUSES = ("AVAILABLE", "BUSY", "MAINTENANCE")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Sector(Base):
    __tablename__ = "sectors"

    sector_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    district: Mapped[str] = mapped_column(String(50))
    cell: Mapped[str | None] = mapped_column(String(50), nullable=True)
    village: Mapped[str | None] = mapped_column(String(50), nullable=True)


class Farmer(Base):
    __tablename__ = "farmers"
    __table_args__ = (
        Index("idx_farmers_user_id", "user_id"),
        Index("idx_farmers_sector_id", "sector_id"),
        Index("idx_farmers_phone", "phone"),
    )

    farmer_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(10))
    cell: Mapped[str | None] = mapped_column(String(50), nullable=True)
    village: Mapped[str | None] = mapped_column(String(50), nullable=True)


class FarmerAdminProfile(Base):
    __tablename__ = "farmer_admin_profiles"
    __table_args__ = (
        Index("idx_farmer_profiles_status", "registration_status"),
        Index("idx_farmer_profiles_registered_at", "registered_at"),
    )

    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE"), primary_key=True
    )
    national_id: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True
    )
    registration_status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", server_default="ACTIVE"
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class Transporter(Base):
    __tablename__ = "transporters"
    __table_args__ = (
        Index("idx_transporters_user_id", "user_id"),
        Index("idx_transporters_sector_id", "sector_id"),
    )

    transporter_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(50))


class Truck(Base):
    __tablename__ = "trucks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('AVAILABLE', 'BUSY', 'MAINTENANCE')",
            name="chk_trucks_status",
        ),
        Index("idx_trucks_transporter_id", "transporter_id"),
        Index("idx_trucks_sector_status", "sector_id", "status"),
        Index("idx_trucks_status", "status"),
    )

    truck_id: Mapped[int] = mapped_column(primary_key=True)
    transporter_id: Mapped[int] = mapped_column(
        ForeignKey("transporters.transporter_id", ondelete="CASCADE")
    )
    plate_number: Mapped[str] = mapped_column(String(15), unique=True)
    capacity_kg: Mapped[float] = mapped_column(Float)
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(
        String(20), default="AVAILABLE", server_default="AVAILABLE"
    )


class TruckOperationalDetail(Base):
    __tablename__ = "truck_operational_details"
    __table_args__ = (Index("idx_truck_details_updated_at", "updated_at"),)

    truck_id: Mapped[int] = mapped_column(
        ForeignKey("trucks.truck_id", ondelete="CASCADE"), primary_key=True
    )
    vehicle_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ColdHub(Base):
    __tablename__ = "cold_hubs"
    __table_args__ = (
        CheckConstraint(
            "available_capacity_kg >= 0 AND available_capacity_kg <= total_capacity_kg",
            name="chk_hub_capacity",
        ),
        Index("idx_hubs_sector_id", "sector_id"),
        Index("idx_hubs_status", "operating_status"),
    )

    hub_id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    total_capacity_kg: Mapped[float] = mapped_column(Float)
    available_capacity_kg: Mapped[float] = mapped_column(Float)
    operating_status: Mapped[str] = mapped_column(
        String(10), default="OPEN", server_default="OPEN"
    )


class ColdHubAccount(Base):
    __tablename__ = "cold_hub_accounts"
    __table_args__ = (Index("idx_hub_accounts_user_id", "user_id"),)

    hub_id: Mapped[int] = mapped_column(
        ForeignKey("cold_hubs.hub_id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), unique=True
    )


class ColdHubCapacityUpdate(Base):
    __tablename__ = "cold_hub_capacity_updates"
    __table_args__ = (
        CheckConstraint(
            "available_capacity_kg >= 0 AND available_capacity_kg <= total_capacity_kg",
            name="chk_hub_capacity_update",
        ),
        Index("idx_hub_capacity_updates_hub_id", "hub_id"),
        Index("idx_hub_capacity_updates_created_at", "created_at"),
    )

    update_id: Mapped[int] = mapped_column(primary_key=True)
    hub_id: Mapped[int] = mapped_column(
        ForeignKey("cold_hubs.hub_id", ondelete="CASCADE")
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    total_capacity_kg: Mapped[float] = mapped_column(Float)
    available_capacity_kg: Mapped[float] = mapped_column(Float)
    produce_type: Mapped[str] = mapped_column(
        String(30), default="tomatoes", server_default="tomatoes"
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
