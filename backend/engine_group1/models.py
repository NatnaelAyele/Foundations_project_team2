"""
SQLAlchemy models for the tables Group 1 (data-prep stage) reads from.

These mirror the shared ERD. If the DB person's schema.py already defines
these tables, don't duplicate them — import theirs instead and delete this
file. This file exists so Group 1's code is runnable and testable on its own
before the schema is wired in.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Farmer(Base):
    __tablename__ = "farmers"

    farmer_id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    sector = Column(String, nullable=False)  # e.g. "Rugarama"

    forecasts = relationship("HarvestForecast", back_populates="farmer")


class HarvestForecast(Base):
    __tablename__ = "harvest_forecasts"

    forecast_id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("farmers.farmer_id"), nullable=False)
    quantity_kg = Column(Numeric, nullable=False)
    harvest_date = Column(Date, nullable=False)
    sector = Column(String, nullable=False)  # denormalised for fast clustering
    status = Column(String, nullable=False, default="pending")
    # pending -> validated forecasts move on to eligible/excluded downstream;
    # 'cancelled' is set by the USSD cancel flow (Flow A), not by the engine.
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="forecasts")
