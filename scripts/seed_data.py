from __future__ import annotations
import argparse
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

# local imports
from app.db import init_db, SessionLocal
from app import models
from app.services.parcels import create_parcel, apply_scan_transition


def wipe_data(db: Session) -> None:
    # simple truncate order: scans -> parcels -> customers
    db.query(models.Scan).delete()
    db.query(models.Parcel).delete()
    db.query(models.Customer).delete()
    db.commit()


def seed_customers(db: Session) -> list[models.Customer]:
    customers = [
        models.Customer(name="ACME SRL", phone="+40 712 345 678"),
        models.Customer(name="Blue Logistics", phone="+40 733 111 222"),
        models.Customer(name="Casa Verde", phone=None),
    ]
    db.add_all(customers)
    db.commit()
    for c in customers:
        db.refresh(c)
    return customers


def new_parcel(
    db: Session,
    customer_id: int,
    weight: float,
    addr_from: str,
    addr_to: str,
) -> models.Parcel:
    p = models.Parcel(
        tracking_code="TMP",
        customer_id=customer_id,
        status="new",
        weight_kg=weight,
        addr_from=addr_from,
        addr_to=addr_to,
    )
    return create_parcel(db, p, p.customer_id)


def seed_parcels_and_scans(db: Session, customers: list[models.Customer]) -> list[models.Parcel]:
    now = datetime.utcnow()

    parcels: list[models.Parcel] = []

    # 1) Parcel delivered (full timeline)
    p1 = new_parcel(
        db, customers[0].id, 1.2, "Depozit Nord, Str A 1", "Ion Pop, Oras Y"
    )
    apply_scan_transition(db, p1, "pickup", now - timedelta(hours=26), "Depozit Nord", "preluat")
    apply_scan_transition(db, p1, "in_transit", now - timedelta(hours=22), "Hub Central", None)
    apply_scan_transition(db, p1, "out_for_delivery", now - timedelta(hours=3), "Oras Y", None)
    apply_scan_transition(db, p1, "delivered", now - timedelta(hours=1), "Oras Y", "predat")
    parcels.append(p1)

    # 2) Parcel in_transit
    p2 = new_parcel(
        db, customers[0].id, 3.5, "Depozit Vest, Str C 9", "SC Alfa, Oras Z"
    )
    apply_scan_transition(db, p2, "pickup", now - timedelta(hours=8), "Depozit Vest", None)
    apply_scan_transition(db, p2, "in_transit", now - timedelta(hours=5), "Hub Central", "plecat spre Est")
    parcels.append(p2)

    # 3) Parcel out_for_delivery
    p3 = new_parcel(
        db, customers[1].id, 0.8, "Depozit Sud, Str D 4", "Maria Ionescu, Oras X"
    )
    apply_scan_transition(db, p3, "pickup", now - timedelta(hours=7), "Depozit Sud", None)
    apply_scan_transition(db, p3, "in_transit", now - timedelta(hours=6), "Hub Central", None)
    apply_scan_transition(db, p3, "out_for_delivery", now - timedelta(hours=1), "Oras X", "plecat la adresa")
    parcels.append(p3)

    # 4) Parcel return (final)
    p4 = new_parcel(
        db, customers[1].id, 5.0, "Depozit Nord, Str A 1", "Client necunoscut, Oras W"
    )
    apply_scan_transition(db, p4, "pickup", now - timedelta(days=1), "Depozit Nord", None)
    apply_scan_transition(db, p4, "in_transit", now - timedelta(hours=18), "Hub Central", None)
    apply_scan_transition(db, p4, "return", now - timedelta(hours=12), "Hub Central", "adresat nerecunoscut")
    parcels.append(p4)

    # 5) Parcel nou (fara scan-uri)
    p5 = new_parcel(
        db, customers[2].id, 2.0, "Depozit Est, Str K 2", "Gheorghe Vlas, Oras V"
    )
    parcels.append(p5)

    return parcels


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed database with sample data.")
    parser.add_argument("--reset", action="store_true", help="wipe tables before seeding")
    args = parser.parse_args()

    # ensure tables exist
    init_db()

    db = SessionLocal()
    try:
        if args.reset:
            wipe_data(db)

        # if DB already has customers, do nothing unless --reset was provided
        existing = db.query(models.Customer).count()
        if existing > 0 and not args.reset:
            print("DB already has data. Use --reset to wipe and reseed.")
            return

        customers = seed_customers(db)
        parcels = seed_parcels_and_scans(db, customers)

        print(f"Seed done: {len(customers)} customers, {len(parcels)} parcels.")
        if parcels:
            print("Example tracking codes:",
                  ", ".join(p.tracking_code for p in parcels[:3]))
    finally:
        db.close()


if __name__ == "__main__":
    main()
