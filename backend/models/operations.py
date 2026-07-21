from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    Time,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


FORECAST_STATUSES = ("PENDING", "ALLOCATED", "CANCELLED")
PLAN_STATUSES = ("RUNNING", "COMPLETED", "FAILED")
TRIP_STATUSES = ("SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED")
ACTIVE_TRIP_STATUSES = ("SCHEDULED", "IN_PROGRESS")
PAYMENT_STATUSES = (
    "CREATED",
    "INITIALIZED",
    "PENDING",
    "PAID",
    "FAILED",
    "CANCELLED",
    "REFUNDED",
)


class HarvestForecast(Base):
    __tablename__ = "harvest_forecasts"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="chk_forecast_quantity"),
        CheckConstraint(
            "LOWER(status) IN ('pending', 'allocated', 'cancelled', 'excluded', 'expired')",
            name="chk_harvest_forecasts_status",
        ),
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
    harvest_time: Mapped[time] = mapped_column(Time, default=time(8, 0), server_default=text("'08:00'"))
    status: Mapped[str] = mapped_column(
        String(10), default="PENDING", server_default="PENDING"
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    requirement: Mapped["ForecastRequirement"] = relationship(
        "ForecastRequirement", back_populates="forecast", uselist=False
    )


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
    forecast: Mapped["HarvestForecast"] = relationship(
        "HarvestForecast", back_populates="requirement"
    )


class CoordinationPlan(Base):
    __tablename__ = "coordination_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RUNNING', 'COMPLETED', 'FAILED')",
            name="chk_coordination_plans_status",
        ),
        Index("idx_plans_sector_id", "sector_id"),
        Index("idx_plans_status", "status"),
    )

    plan_id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int] = mapped_column(
        ForeignKey("sectors.sector_id", ondelete="RESTRICT")
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[str] = mapped_column(
        String(50), default="RUNNING", server_default="RUNNING"
    )


class TripAllocation(Base):
    __tablename__ = "trip_allocations"
    __table_args__ = (
        CheckConstraint("total_load_kg > 0", name="chk_alloc_load"),
        CheckConstraint(
            "status IN ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="chk_trip_allocations_status",
        ),
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
        String(20), default="SCHEDULED", server_default="SCHEDULED"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    forecast_allocations: Mapped[list["ForecastAllocation"]] = relationship(
        "ForecastAllocation",
        back_populates="trip_allocation",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="trip_allocation",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="trip_allocation",
    )


class ForecastAllocation(Base):
    __tablename__ = "forecast_allocations"

    allocation_id: Mapped[int] = mapped_column(
        ForeignKey("trip_allocations.allocation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("harvest_forecasts.forecast_id", ondelete="CASCADE"),
        primary_key=True,
    )
    allocated_quantity_kg: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    trip_allocation: Mapped["TripAllocation"] = relationship(
        "TripAllocation",
        back_populates="forecast_allocations",
    )
    forecast: Mapped["HarvestForecast"] = relationship("HarvestForecast")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payments_amount"),
        CheckConstraint(
            "status IN ('CREATED', 'INITIALIZED', 'PENDING', 'PAID', 'FAILED', 'CANCELLED', 'REFUNDED')",
            name="chk_payments_status",
        ),
        Index("idx_payments_allocation_id", "allocation_id"),
        Index("idx_payments_farmer_id", "farmer_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_tx_ref", "tx_ref", unique=True),
        Index("idx_payments_payment_reference", "payment_reference", unique=True),
        Index("idx_payments_transaction_id", "transaction_id", unique=True),
    )

    payment_id: Mapped[int] = mapped_column(primary_key=True)
    allocation_id: Mapped[int | None] = mapped_column(
        ForeignKey("trip_allocations.allocation_id", ondelete="CASCADE"), nullable=True
    )
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE")
    )
    payer_type: Mapped[str] = mapped_column(String(50))
    payee_type: Mapped[str] = mapped_column(String(50))
    payer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payee_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(
        String(3), default="RWF", server_default="RWF"
    )
    purpose: Mapped[str] = mapped_column(String(100))
    payment_method: Mapped[str] = mapped_column(
        String(30), default="FLUTTERWAVE", server_default="FLUTTERWAVE"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="CREATED", server_default="CREATED"
    )
    payment_reference: Mapped[str] = mapped_column(String(100), unique=True)
    flutterwave_ref: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    tx_ref: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    payment_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trip_allocation: Mapped["TripAllocation | None"] = relationship(
        "TripAllocation",
        back_populates="payments",
    )
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="payments")


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        Index("idx_payment_webhook_events_payment_id", "payment_id"),
        Index("idx_payment_webhook_events_tx_ref", "tx_ref"),
    )

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.payment_id", ondelete="SET NULL"), nullable=True
    )
    tx_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    payment: Mapped["Payment | None"] = relationship("Payment")


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
    status: Mapped[str] = mapped_column(String(20))
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
    reason_detail: Mapped[str | None] = mapped_column(String, nullable=True)
    excluded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notif_trip_id", "related_trip_id"),
        Index("idx_notif_phone", "recipient_phone"),
        Index(
            "idx_notif_queued",
            "notification_id",
            postgresql_where=text("LOWER(status) IN ('queued', 'pending')"),
            sqlite_where=text("LOWER(status) IN ('queued', 'pending')"),
        ),
    )

    notification_id: Mapped[int] = mapped_column(primary_key=True)
    recipient_type: Mapped[str] = mapped_column(
        String(50), default="FARMER", server_default="FARMER"
    )
    recipient_phone: Mapped[str] = mapped_column(String(15))
    channel: Mapped[str] = mapped_column(String(50), default="SMS", server_default="SMS")
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending"
    )
    sent_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, server_default=func.now()
    )
    related_trip_id: Mapped[int | None] = mapped_column(
        ForeignKey("trip_allocations.allocation_id", ondelete="SET NULL"), nullable=True
    )
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE"), nullable=True
    )
    notification_type: Mapped[str] = mapped_column(
        String(40), default="GENERAL", server_default="GENERAL"
    )
    language: Mapped[str] = mapped_column(String(5), default="en", server_default="en")
    trip_allocation: Mapped["TripAllocation | None"] = relationship(
        "TripAllocation",
        back_populates="notifications",
    )
    farmer: Mapped["Farmer | None"] = relationship(
        "Farmer",
        back_populates="notifications",
    )
