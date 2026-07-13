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


class Transporter(Base):
    __tablename__ = "transporters"
    __table_args__ = (
        Index("idx_transporters_user_id", "user_id"),
        Index("idx_transporters_sector_id", "sector_id"),
    )

    transporter_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), unique=True
    )
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(50), unique=True)


class Truck(Base):
    __tablename__ = "trucks"
    __table_args__ = (
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
    status: Mapped[str] = mapped_column(String(10), default="IDLE", server_default="IDLE")


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
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), unique=True
    )
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(15), unique=True, nullable=True)
    total_capacity_kg: Mapped[float] = mapped_column(Float)
    available_capacity_kg: Mapped[float] = mapped_column(Float)
    operating_status: Mapped[str] = mapped_column(
        String(10), default="OPEN", server_default="OPEN"
    )
