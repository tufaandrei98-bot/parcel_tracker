from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Parcel, Customer
from app.schemas import ParcelOut, ParcelCreate, TimelineOut
from app.services.parcels import find_parcel_by_code, create_parcel
from app.routers.customers import parse_sort, apply_sort

router = APIRouter(prefix="/parcels", tags=["parcels"])


@router.post("", response_model=ParcelOut, status_code=201)
def create_parcel_endpoint(payload: ParcelCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(404, "customer not found")

    parcel = Parcel(
        tracking_code="TMP",  # temporary; will be replaced in service after flush
        customer_id=payload.customer_id,
        status="new",
        weight_kg=payload.weight_kg,
        addr_from=payload.addr_from,
        addr_to=payload.addr_to,
    )
    parcel = create_parcel(db, parcel, payload.customer_id)
    return parcel


@router.get("", response_model=List[ParcelOut])
def list_parcels(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = "created_at,desc",
):
    stmt = select(Parcel)

    if status:
        stmt = stmt.where(Parcel.status == status)
    if customer_id:
        stmt = stmt.where(Parcel.customer_id == customer_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Parcel.tracking_code.ilike(like),
                Parcel.addr_from.ilike(like),
                Parcel.addr_to.ilike(like),
            )
        )

    field, order = parse_sort(
        sort, {"created_at", "status", "id", "tracking_code", "delivered_at"}, "created_at"
    )
    stmt = apply_sort(stmt, Parcel, field, order)
    stmt = stmt.offset((page - 1) * size).limit(size)
    rows = db.execute(stmt).scalars().all()
    return rows


@router.get("/{tracking_code}", response_model=ParcelOut)
def get_parcel(tracking_code: str, db: Session = Depends(get_db)):
    parcel = find_parcel_by_code(db, tracking_code)
    if not parcel:
        raise HTTPException(404, "parcel not found")
    return parcel


@router.get("/{tracking_code}/timeline", response_model=TimelineOut)
def get_timeline(tracking_code: str, db: Session = Depends(get_db)):
    parcel = find_parcel_by_code(db, tracking_code)
    if not parcel:
        raise HTTPException(404, "parcel not found")
    # order scans by ts asc
    scans = sorted(parcel.scans, key=lambda s: s.ts)
    events = [
        TimelineEvent(ts=s.ts, type=s.type, location=s.location, note=s.note)
        for s in scans
    ]
    return TimelineOut(tracking_code=tracking_code, events=events)
