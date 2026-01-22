from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# Common helpers
class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


# Customers
class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    phone: Optional[str] = Field(pattern=r'^[0-9 +()-]{7,20}$')


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    phone: Optional[str] = Field(pattern=r'^[0-9 +()-]{7,20}$')


class CustomerOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Parcels
class ParcelCreate(BaseModel):
    customer_id: int
    weight_kg: float = Field(ge=0)
    addr_from: str = Field(min_length=1, max_length=200)
    addr_to: str = Field(min_length=1, max_length=200)


class ParcelUpdate(BaseModel):
    weight_kg: Optional[float] = Field(default=None, ge=0)
    addr_from: Optional[str] = Field(default=None, min_length=1, max_length=200)
    addr_to: Optional[str] = Field(default=None, min_length=1, max_length=200)


class ParcelOut(BaseModel):
    id: int
    tracking_code: str
    customer_id: int
    status: str
    weight_kg: float
    addr_from: str
    addr_to: str
    created_at: datetime
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Scans
class ScanCreate(BaseModel):
    type: str
    location: str
    ts: datetime
    note: Optional[str] = None


class ScanOut(BaseModel):
    id: int
    parcel_id: int
    type: str
    location: str
    ts: datetime
    note: Optional[str]

    class Config:
        from_attributes = True


# Timeline
class TimelineEvent(BaseModel):
    ts: datetime
    type: str
    location: str
    note: Optional[str] = None


class TimelineOut(BaseModel):
    tracking_code: str
    events: List[TimelineEvent]
