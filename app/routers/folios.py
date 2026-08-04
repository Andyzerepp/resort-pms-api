from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from app.core.database import get_db
from app.core.deps import get_or_404
from app.models.models import Folio, FolioCharge, Payment, Housekeeping, Reservation, User
from app.schemas.folio import (
    FolioResponse, FolioChargeCreate, FolioChargeResponse, PaymentCreate, PaymentResponse
)
from app.core.auth import require_role, get_current_user
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.auth import require_role, get_current_user, verify_password

router = APIRouter(
    prefix="/folios",
    tags=["Folios"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/{folio_id}", response_model=FolioResponse)
def get_folio(folio_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return get_or_404(db, Folio, folio_id, "Folio not found")


@router.post("/{folio_id}/charges", response_model=FolioChargeResponse, status_code=201)
def add_charge(
    folio_id: str,
    data: FolioChargeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk"))
):
    folio = get_or_404(db, Folio, folio_id, "Folio not found")
    if folio.status not in ["open", "settled"]:
        raise HTTPException(status_code=400, detail="Cannot add charges to this folio")

    if data.amount is None or data.amount <= 0:
        raise HTTPException(status_code=400, detail="Charge amount must be greater than ₱0")
    if not data.description or not data.description.strip():
        raise HTTPException(status_code=400, detail="Charge description is required")

    charge_data = data.model_dump()
    charge_data["posted_by"] = current_user.username
    charge = FolioCharge(folio_id=folio_id, **charge_data)
    db.add(charge)

    folio.total_charges = Decimal(str(folio.total_charges)) + Decimal(str(data.amount))
    folio.balance = Decimal(str(folio.total_charges)) - Decimal(str(folio.total_payments))
    if folio.balance > 0:
        folio.status = "open"

    db.commit()
    db.refresh(charge)
    return charge


@router.post("/{folio_id}/payments", response_model=PaymentResponse, status_code=201)
def add_payment(
    folio_id: str,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk"))
):
    folio = get_or_404(db, Folio, folio_id, "Folio not found")
    if folio.status not in ["open", "settled"]:
        raise HTTPException(status_code=400, detail="Folio is closed")

    if data.amount is None or data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than ₱0")

    reservation = db.query(Reservation).filter(
        Reservation.id == folio.reservation_id
    ).first()
    if reservation and reservation.status == "checkout_requested":
        open_inspection = db.query(Housekeeping).filter(
            Housekeeping.room_id.in_([rr.room_id for rr in reservation.reservation_rooms]),
            Housekeeping.task_type == "pre_checkout_inspection",
            Housekeeping.status.notin_(["inspected"])
        ).first()
        if open_inspection:
            raise HTTPException(
                status_code=400,
                detail="Cannot process payment — housekeeping inspection is still pending"
            )

    if data.method != "cash" and not (data.reference_no and data.reference_no.strip()):
        raise HTTPException(
            status_code=400,
            detail=f"Reference number is required for {data.method.replace('_', ' ')} payments"
        )

    balance = Decimal(str(folio.balance))
    tendered = Decimal(str(data.amount))

    if data.method == "cash":
        recorded_amount = min(tendered, balance) if balance > 0 else tendered
        change_given = tendered - recorded_amount if tendered > recorded_amount else Decimal("0")
        amount_tendered = tendered
    else:
        recorded_amount = min(tendered, balance) if balance > 0 else tendered
        change_given = None
        amount_tendered = None

    payment = Payment(
        folio_id=folio_id,
        method=data.method,
        amount=recorded_amount,
        amount_tendered=amount_tendered,
        change_given=change_given,
        reference_no=data.reference_no,
        received_by=current_user.username,
    )
    db.add(payment)

    folio.total_payments = Decimal(str(folio.total_payments)) + recorded_amount
    folio.balance = Decimal(str(folio.total_charges)) - Decimal(str(folio.total_payments))

    if folio.balance <= 0:
        folio.balance = Decimal("0")
        if reservation and reservation.status == "checked_out":
            folio.status = "settled"

    db.commit()
    db.refresh(payment)
    return payment

class VoidChargeRequest(BaseModel):
    admin_username: str
    admin_password: str


@router.patch("/{folio_id}/charges/{charge_id}/void", response_model=FolioChargeResponse)
def void_charge(
    folio_id: str,
    charge_id: str,
    data: VoidChargeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk"))
):
    # Supervisor override — verify admin credentials supplied at the moment of the void
    admin = db.query(User).filter(User.username == data.admin_username).first()
    if not admin or not verify_password(data.admin_password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid supervisor credentials")
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Supervisor override requires an admin account")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="That admin account is inactive")

    folio = get_or_404(db, Folio, folio_id, "Folio not found")
    charge = get_or_404(db, FolioCharge, charge_id, "Charge not found")

    if charge.folio_id != folio_id:
        raise HTTPException(status_code=400, detail="Charge does not belong to this folio")
    if charge.voided:
        raise HTTPException(status_code=400, detail="Charge is already voided")
    if folio.status not in ["open", "settled"]:
        raise HTTPException(status_code=400, detail="Cannot void charges on a closed folio")

    charge.voided = True
    charge.voided_by = admin.username          # the authorizing admin, not the FD on shift
    charge.voided_at = datetime.now(timezone.utc)

    folio.total_charges = Decimal(str(folio.total_charges)) - Decimal(str(charge.amount))
    folio.balance = Decimal(str(folio.total_charges)) - Decimal(str(folio.total_payments))

    if folio.balance <= 0:
        folio.balance = Decimal("0")

    db.commit()
    db.refresh(charge)
    return charge