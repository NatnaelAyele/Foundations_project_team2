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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class HarvestForecast(Base):
    __tablename__ = "harvest_forecasts"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="chk_forecast_quantity"),
        Index("idx_forecasts_farmer_id", "farmer_id"),
        Index("idx_forecasts_status_date", "status", "harvest_date"),
        Index("idx_forecasts_harvest_date", "harvest_date"),
    )

    forecast_id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE")
    )
    quantity_kg: Mapped[float] = mapped_column(Float)
    harvest_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(10), default="PENDING", server_default="PENDING"
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ForecastRequirement(Base):
    __tablename__ = "forecast_requirements"
    __table_args__ = (
        Index("idx_forecast_requirements_transport", "needs_transport"),
        Index("idx_forecast_requirements_storage", "needs_storage"),
        Index("idx_forecast_requirements_source", "source"),
    )

    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("harvest_forecasts.forecast_id", ondelete="CASCADE"),
        primary_key=True,
    )
    needs_transport: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("TRUE")
    )
    needs_storage: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("TRUE")
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(
        String(10), default="USSD", server_default="USSD"
    )


class CoordinationPlan(Base):
    __tablename__ = "coordination_plans"
    __table_args__ = (
        Index("idx_plans_sector_id", "sector_id"),
        Index("idx_plans_status", "status"),
    )

    plan_id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[str] = mapped_column(
        String(50), default="DRAFT", server_default="DRAFT"
    )


class TripAllocation(Base):
    __tablename__ = "trip_allocations"
    __table_args__ = (
        CheckConstraint("total_load_kg > 0", name="chk_alloc_load"),
        Index("idx_alloc_plan_id", "plan_id"),
        Index("idx_alloc_truck_id", "truck_id"),
        Index("idx_alloc_hub_id", "hub_id"),
        Index("idx_alloc_sector_id", "sector_id"),
        Index("idx_alloc_status", "status"),
        Index("idx_alloc_pickup_start", "pickup_start"),
    )

    allocation_id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("coordination_plans.plan_id", ondelete="CASCADE")
    )
    truck_id: Mapped[int] = mapped_column(
        ForeignKey("trucks.truck_id", ondelete="RESTRICT")
    )
    hub_id: Mapped[int] = mapped_column(
        ForeignKey("cold_hubs.hub_id", ondelete="RESTRICT")
    )
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    total_load_kg: Mapped[float] = mapped_column(Float)
    pickup_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimated_hub_arrival: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), default="SCHEDULED", server_default="SCHEDULED"
    )


class HubAllocationReceipt(Base):
    __tablename__ = "hub_allocation_receipts"
    __table_args__ = (
        CheckConstraint("received_quantity_kg > 0", name="chk_hub_receipt_quantity"),
        Index("idx_hub_receipts_confirmed_at", "confirmed_at"),
        Index("idx_hub_receipts_confirmed_by", "confirmed_by_user_id"),
    )

    allocation_id: Mapped[int] = mapped_column(
        ForeignKey("trip_allocations.allocation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    confirmed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    received_quantity_kg: Mapped[float] = mapped_column(Float)


class TripStatusEvent(Base):
    __tablename__ = "trip_status_events"
    __table_args__ = (
        Index("idx_trip_status_events_allocation", "allocation_id"),
        Index("idx_trip_status_events_status_time", "status", "created_at"),
    )

    event_id: Mapped[int] = mapped_column(primary_key=True)
    allocation_id: Mapped[int] = mapped_column(
        ForeignKey("trip_allocations.allocation_id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(10))
    changed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ExcludedTrip(Base):
    __tablename__ = "excluded_trips"
    __table_args__ = (
        Index("idx_excl_forecast_id", "forecast_id"),
        Index("idx_excl_plan_id", "plan_id"),
        Index("idx_excl_reason", "reason_code"),
    )

    exclusion_id: Mapped[int] = mapped_column(primary_key=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("harvest_forecasts.forecast_id", ondelete="CASCADE")
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("coordination_plans.plan_id", ondelete="CASCADE")
    )
    reason_code: Mapped[str] = mapped_column(String(50))
    excluded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notif_trip_id", "related_trip_id"),
        Index("idx_notif_phone", "recipient_phone"),
        Index(
            "idx_notif_queued",
            "notification_id",
            postgresql_where=text("status = 'QUEUED'"),
            sqlite_where=text("status = 'QUEUED'"),
        ),
    )

    notification_id: Mapped[int] = mapped_column(primary_key=True)
    recipient_type: Mapped[str] = mapped_column(String(50))
    recipient_phone: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50), default="SMS", server_default="SMS")
    message: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(10), default="QUEUED", server_default="QUEUED"
    )
    sent_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    related_trip_id: Mapped[int | None] = mapped_column(
        ForeignKey("trip_allocations.allocation_id", ondelete="SET NULL"), nullable=True
    )
