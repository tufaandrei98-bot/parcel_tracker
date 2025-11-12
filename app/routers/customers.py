from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Customer
from app.schemas import CustomerOut, CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(name=payload.name, phone=payload.phone)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = "created_at,desc",
):
    stmt = select(Customer)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(Customer.name.ilike(like))
    field, order = parse_sort(sort, {"created_at", "name", "id"}, default="created_at")
    stmt = apply_sort(stmt, Customer, field, order)
    stmt = stmt.offset((page - 1) * size).limit(size)
    rows = db.execute(stmt).scalars().all()
    return rows


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if not obj:
        raise HTTPException(404, "customer not found")
    return obj


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)
):
    obj = db.get(Customer, customer_id)
    if not obj:
        raise HTTPException(404, "customer not found")
    if payload.name is not None:
        obj.name = payload.name
    if payload.phone is not None:
        obj.phone = payload.phone
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if not obj:
        raise HTTPException(404, "customer not found")
    db.delete(obj)
    db.commit()
    return None


# Helpers
def parse_sort(raw: str, allowed_fields: set[str], default: str):
    parts = raw.split(",")
    field = parts[0] if parts else default
    order = parts[1] if len(parts) > 1 else "desc"
    if field not in allowed_fields:
        field = default
    order = "desc" if order.lower() == "desc" else "asc"
    return field, order


def apply_sort(stmt, model, field: str, order: str):
    column = getattr(model, field)
    return stmt.order_by(column.desc() if order == "desc" else column.asc())
