from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Parcel

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/parcels-by-status")
def parcels_by_status(
    from_: str = Query(..., alias="from"),
    to: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
) -> Dict[str, int]:
    try:
        dt_from = datetime.fromisoformat(from_)
        dt_to = datetime.fromisoformat(to)
    except ValueError:
        raise HTTPException(400, "invalid date format, expected YYYY-MM-DD")

    if dt_from > dt_to:
        raise HTTPException(400, "from must be <= to")

    # include whole "to" day
    dt_to_end = dt_to + timedelta(days=1)

    stmt = (
        select(Parcel.status, func.count(Parcel.id))
        .where(Parcel.created_at >= dt_from, Parcel.created_at < dt_to_end)
        .group_by(Parcel.status)
    )
    rows = db.execute(stmt).all()

    result = {
        "new": 0,
        "pickup": 0,
        "in_transit": 0,
        "out_for_delivery": 0,
        "delivered": 0,
        "return": 0,
    }
    for status, cnt in rows:
        if status in result:
            result[status] = cnt
    return result
