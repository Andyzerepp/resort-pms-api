from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date, datetime, timezone
from app.models.models import (
    Reservation, ReservationRoom, Room, Folio, FolioCharge, Housekeeping
)
from app.services.availability_service import is_room_available
from app.services.folio_service import post_charge


def create_reservation(db: Session, guest_id: str, check_in: date, check_out: date, source: str, rooms: list):
    """Create a reservation, assign rooms, and auto-create a folio with room charges."""
    if check_out <= check_in:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")

    # Validate and check availability for all rooms
    for room_data in rooms:
        room = db.query(Room).filter(Room.id == room_data.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {room_data.room_id} not found")
        if not is_room_available(db, room_data.room_id, check_in, check_out):
            raise HTTPException(
                status_code=400,
                detail=f"Room {room.room_number} is not available for the selected dates"
            )

    # Calculate total
    nights = (check_out - check_in).days
    total = sum(float(r.rate_at_booking) * nights for r in rooms)

    # Create reservation
    reservation = Reservation(
        guest_id=guest_id,
        check_in=check_in,
        check_out=check_out,
        source=source,
        total_amount=total,
        status="confirmed",
        confirmed_at=datetime.now(timezone.utc)
    )
    db.add(reservation)
    db.flush()

    # Assign rooms
    for room_data in rooms:
        res_room = ReservationRoom(
            reservation_id=reservation.id,
            room_id=room_data.room_id,
            rate_at_booking=room_data.rate_at_booking
        )
        db.add(res_room)

    # Auto-create folio with zero totals
    folio = Folio(
            reservation_id=reservation.id,
            total_charges=0,
            total_payments=0,
            balance=0,
            status="open"
        )
    db.add(folio)
    db.flush()

    # Post room charge — this updates the folio totals
    post_charge(
        db=db,
        folio_id=folio.id,
        charge_type="room",
        description=f"Room charge — {nights} night(s)",
        amount=total
    )

    db.commit()
    db.refresh(reservation)
    return reservation


def check_in_reservation(db: Session, reservation_id: str):
    """Check in a reservation — mark rooms as occupied."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.status != "confirmed":
        raise HTTPException(status_code=400, detail="Only confirmed reservations can be checked in")

    for res_room in reservation.reservation_rooms:
        res_room.room.status = "occupied"

    reservation.status = "checked_in"
    reservation.checked_in_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reservation)
    return reservation

def request_checkout(db: Session, reservation_id: str):
    """Front desk requests checkout — triggers housekeeping pre-checkout inspection."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.status != "checked_in":
        raise HTTPException(status_code=400, detail="Only checked-in reservations can request checkout")

    reservation.status = "checkout_requested"
    reservation.checkout_requested_at = datetime.now(timezone.utc)

    # Create a high-priority pre-checkout inspection task for each room
    for res_room in reservation.reservation_rooms:
        inspection = Housekeeping(
            room_id=res_room.room_id,
            reservation_id=reservation.id,
            task_type="pre_checkout_inspection",
            status="dirty",
            priority="high",
            created_at=datetime.now(timezone.utc)
        )
        db.add(inspection)

    db.commit()
    db.refresh(reservation)
    return reservation

def check_out_reservation(db: Session, reservation_id: str):
    """Final check out — only allowed after checkout was requested and inspection cleared."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.status != "checkout_requested":
        raise HTTPException(status_code=400, detail="Checkout must be requested first — use Request Checkout")

    # Block checkout if balance is outstanding
    folio = reservation.folio
    if folio and float(folio.balance) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot check out — outstanding balance of ₱{folio.balance:,.2f}"
        )

    # Verify all pre-checkout inspections are cleared (not still flagged with issues)
    for res_room in reservation.reservation_rooms:
        open_issue = db.query(Housekeeping).filter(
            Housekeeping.room_id == res_room.room_id,
            Housekeeping.task_type == "pre_checkout_inspection",
            Housekeeping.status == "room_flagged"
        ).first()
        if open_issue:
            raise HTTPException(
                status_code=400,
                detail=f"Room {res_room.room.room_number} has an unresolved issue — resolve before checkout"
            )

    # Mark rooms as dirty and create post-checkout cleaning tasks
    for res_room in reservation.reservation_rooms:
        res_room.room.status = "dirty"

        # If an older post-checkout task for this room is still pending,
        # update it instead of stacking a duplicate card on top of it
        existing_task = db.query(Housekeeping).filter(
            Housekeeping.room_id == res_room.room_id,
            Housekeeping.task_type == "post_checkout_clean",
            Housekeeping.status == "dirty"
        ).first()

        if existing_task:
            existing_task.reservation_id = reservation.id
            existing_task.created_at = datetime.now(timezone.utc)
        else:
            hk = Housekeeping(
                room_id=res_room.room_id,
                reservation_id=reservation.id,
                task_type="post_checkout_clean",
                status="dirty",
                priority="normal"
            )
            db.add(hk)

    # Settle the folio now that checkout is actually happening — balance is
    # already guaranteed ≤ 0 at this point, since we blocked above otherwise
    if folio:
        folio.status = "settled"

    reservation.status = "checked_out"
    reservation.checked_out_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reservation)
    return reservation


def cancel_reservation(db: Session, reservation_id: str, cancelled_by: str = None, reason: str = None, notes: str = None):
    """Cancel a reservation — only allowed if not yet checked in."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.status in ["checked_in", "checkout_requested"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a checked-in reservation — check out first"
        )
    if reservation.status in ["checked_out", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Reservation is already {reservation.status}"
        )

    reservation.status = "cancelled"
    reservation.cancelled_at = datetime.now(timezone.utc)
    reservation.cancelled_by = cancelled_by
    reservation.cancellation_reason = reason
    reservation.cancellation_notes = notes
    db.commit()
    db.refresh(reservation)
    return reservation