from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_or_404
from app.models.models import Reservation, User
from app.schemas.reservation import ReservationCreate, ReservationUpdate, ReservationResponse
from app.services import reservation_service
from app.core.auth import require_role, get_current_user
from pydantic import BaseModel

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[ReservationResponse])
def get_reservations(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return db.query(Reservation).all()


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return get_or_404(db, Reservation, reservation_id, "Reservation not found")


@router.post("/", response_model=ReservationResponse, status_code=201)
def create_reservation(data: ReservationCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return reservation_service.create_reservation(
        db=db,
        guest_id=data.guest_id,
        check_in=data.check_in,
        check_out=data.check_out,
        source=data.source,
        rooms=data.rooms
    )


@router.patch("/{reservation_id}/check-in", response_model=ReservationResponse)
def check_in(reservation_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return reservation_service.check_in_reservation(db, reservation_id)

@router.patch("/{reservation_id}/request-checkout", response_model=ReservationResponse)
def request_checkout(reservation_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return reservation_service.request_checkout(db, reservation_id)

@router.patch("/{reservation_id}/check-out", response_model=ReservationResponse)
def check_out(reservation_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return reservation_service.check_out_reservation(db, reservation_id)


class CancelRequest(BaseModel):
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancellation_notes: Optional[str] = None

@router.patch("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel(reservation_id: str, data: CancelRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return reservation_service.cancel_reservation(
        db=db,
        reservation_id=reservation_id,
        cancelled_by=data.cancelled_by,
        reason=data.cancellation_reason,
        notes=data.cancellation_notes
    )


@router.delete("/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    reservation = get_or_404(db, Reservation, reservation_id, "Reservation not found")
    db.delete(reservation)
    db.commit()