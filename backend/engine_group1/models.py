# These are the tables I read from - farmers, sectors, harvest_forecasts.
# If the DB person already has these in the shared models/ folder, delete this and import theirs.
# Matches the real seed_data.sql: sectors is its own table, farmer.name/farmer.phone, harvest_date is a timestamp.

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Sector(Base):
    __tablename__ = "sectors"

    sector_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    district = Column(String)
    cell = Column(String)
    village = Column(String)


class Farmer(Base):
    __tablename__ = "farmers"

    farmer_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # links to users table, not modelled here
    sector_id = Column(Integer, ForeignKey("sectors.sector_id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    cell = Column(String)
    village = Column(String)

    sector = relationship("Sector")
    forecasts = relationship("HarvestForecast", back_populates="farmer")


class HarvestForecast(Base):
    __tablename__ = "harvest_forecasts"

    forecast_id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("farmers.farmer_id"), nullable=False)
    quantity_kg = Column(Numeric, nullable=False)
    harvest_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="forecasts")
