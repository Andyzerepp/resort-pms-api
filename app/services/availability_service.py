from sqlalchemy.orm import Session
from datetime import date
from app.models.models import Room, ReservationRoom, Reservation


def get_available_rooms(db: Session, check_in: date, check_out: date):
    """Returns all rooms not booked for the given date range."""
    booked_room_ids = db.query(ReservationRoom.room_id).join(Reservation).filter(
        Reservation.status.in_(["confirmed", "checked_in"]),
        Reservation.check_in < check_out,
        Reservation.check_out > check_in
    ).subquery()

    return db.query(Room).filter(
        Room.status == "available",
        Room.id.notin_(booked_room_ids)
    ).all()


def is_room_available(db: Session, room_id: str, check_in: date, check_out: date, exclude_reservation_id: str = None):
    """Returns True if the room is available for the given date range."""
    query = db.query(ReservationRoom).join(Reservation).filter(
        ReservationRoom.room_id == room_id,
        Reservation.status.in_(["confirmed", "checked_in"]),
        Reservation.check_in < check_out,
        Reservation.check_out > check_in
    )
    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)
    return query.first() is None