from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parcels: Mapped[List["Parcel"]] = relationship("Parcel", back_populates="customer")


class Parcel(Base):
    __tablename__ = "parcels"
    __table_args__ = (UniqueConstraint("tracking_code", name="uq_parcels_tracking_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tracking_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(24), default="new", index=True)
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    addr_from: Mapped[str] = mapped_column(String(200))
    addr_to: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="parcels")
    scans: Mapped[List["Scan"]] = relationship(
        "Scan", back_populates="parcel", cascade="all, delete-orphan"
    )


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), nullable=False, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    location: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(32))
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    parcel: Mapped["Parcel"] = relationship("Parcel", back_populates="scans")
