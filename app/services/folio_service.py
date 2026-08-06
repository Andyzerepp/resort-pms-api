from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Folio, FolioCharge, Payment


def get_folio_by_reservation(db: Session, reservation_id: str):
    """Get a folio by reservation id."""
    folio = db.query(Folio).filter(Folio.reservation_id == reservation_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    return folio


def recompute_folio_totals(db: Session, folio: Folio) -> Folio:
    """Derive total_charges/total_payments/balance from the actual charge and
    payment rows via SQL SUM, rather than trusting incrementally-maintained
    values. Call this after any write that touches a folio's charges or
    payments, and on read, so a crash mid-request can't leave the stored
    totals silently desynced from the rows they're supposed to reflect.

    Does not touch folio.status — status transitions are the caller's
    responsibility, since the right transition depends on context (e.g.
    reopening on a new charge vs. settling on checkout).
    """
    total_charges = db.query(func.coalesce(func.sum(FolioCharge.amount), 0)).filter(
        FolioCharge.folio_id == folio.id,
        FolioCharge.voided.is_(False),
    ).scalar()
    total_payments = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.folio_id == folio.id,
    ).scalar()

    total_charges = Decimal(str(total_charges))
    total_payments = Decimal(str(total_payments))

    folio.total_charges = total_charges
    folio.total_payments = total_payments
    folio.balance = max(total_charges - total_payments, Decimal("0"))
    return folio


def post_charge(db: Session, folio_id: str, charge_type: str, description: str, amount: float):
    """Add a charge to a folio and recompute totals from source."""
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    if folio.status != "open":
        raise HTTPException(status_code=400, detail="Cannot add charges to a closed folio")

    charge = FolioCharge(
        folio_id=folio_id,
        charge_type=charge_type,
        description=description,
        amount=amount
    )
    db.add(charge)
    db.flush()

    recompute_folio_totals(db, folio)
    return charge