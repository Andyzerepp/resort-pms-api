from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Folio, FolioCharge, Payment


def get_folio_by_reservation(db: Session, reservation_id: str):
    """Get a folio by reservation id."""
    folio = db.query(Folio).filter(Folio.reservation_id == reservation_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    return folio


def post_charge(db: Session, folio_id: str, charge_type: str, description: str, amount: float):
    """Add a charge to a folio and recalculate balance."""
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

    folio.total_charges = float(folio.total_charges) + amount
    folio.balance = float(folio.total_charges) - float(folio.total_payments)

    db.flush()
    return charge


def post_payment(db: Session, folio_id: str, method: str, amount: float, reference_no: str = None):
    """Record a payment and auto-settle folio if fully paid."""
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    if folio.status != "open":
        raise HTTPException(status_code=400, detail="Folio is already settled")

    payment = Payment(
        folio_id=folio_id,
        method=method,
        amount=amount,
        reference_no=reference_no
    )
    db.add(payment)

    folio.total_payments = float(folio.total_payments) + amount
    folio.balance = float(folio.total_charges) - float(folio.total_payments)

    if folio.balance <= 0:
        folio.balance = 0

    db.flush()
    return payment


def recalculate_folio(db: Session, folio_id: str):
    """Recalculate folio totals from scratch based on actual charges and payments."""
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")

    total_charges = sum(float(c.amount) for c in folio.charges)
    total_payments = sum(float(p.amount) for p in folio.payments)
    balance = total_charges - total_payments

    folio.total_charges = total_charges
    folio.total_payments = total_payments
    folio.balance = max(balance, 0)

    if balance <= 0:
        folio.status = "settled"

    db.flush()
    return folio