from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.core.database import get_db
from app.core.deps import get_or_404
from app.models.models import Room, RoomType, ReservationRoom, Reservation, User
from app.schemas.room import (
    RoomCreate, RoomUpdate, RoomResponse,
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse
)
from app.core.auth import require_role, get_current_user

router = APIRouter(
    tags=["Rooms"],
    dependencies=[Depends(get_current_user)],
)


# ── Room Types ──────────────────────────────────────────────
@router.get("/room-types", response_model=List[RoomTypeResponse])
def get_room_types(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return db.query(RoomType).all()


@router.post("/room-types", response_model=RoomTypeResponse, status_code=201)
def create_room_type(data: RoomTypeCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    room_type = RoomType(**data.model_dump())
    db.add(room_type)
    db.commit()
    db.refresh(room_type)
    return room_type


@router.patch("/room-types/{room_type_id}", response_model=RoomTypeResponse)
def update_room_type(room_type_id: str, data: RoomTypeUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    room_type = get_or_404(db, RoomType, room_type_id, "Room type not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(room_type, field, value)
    db.commit()
    db.refresh(room_type)
    return room_type


@router.delete("/room-types/{room_type_id}", status_code=204)
def delete_room_type(room_type_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    room_type = get_or_404(db, RoomType, room_type_id, "Room type not found")
    rooms = db.query(Room).filter(Room.room_type_id == room_type_id).first()
    if rooms:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete room type — there are rooms assigned to it. Remove the rooms first."
        )
    db.delete(room_type)
    db.commit()


# ── Rooms ───────────────────────────────────────────────────
@router.get("/rooms", response_model=List[RoomResponse])
def get_rooms(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk", "housekeeping"))):
    return db.query(Room).all()


@router.get("/rooms/available", response_model=List[RoomResponse])
def get_available_rooms(
    check_in: date,
    check_out: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk"))
):
    booked_room_ids = db.query(ReservationRoom.room_id).join(Reservation).filter(
        Reservation.status.in_(["confirmed", "checked_in"]),
        Reservation.check_in < check_out,
        Reservation.check_out > check_in
    ).subquery()

    available = db.query(Room).filter(
        Room.status == "available",
        Room.id.notin_(booked_room_ids)
    ).all()
    return available


@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(room_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return get_or_404(db, Room, room_id, "Room not found")


@router.post("/rooms", response_model=RoomResponse, status_code=201)
def create_room(data: RoomCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    room_type = get_or_404(db, RoomType, data.room_type_id, "Room type not found")
    room = Room(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.patch("/rooms/{room_id}", response_model=RoomResponse)
def update_room(room_id: str, data: RoomUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    room = get_or_404(db, Room, room_id, "Room not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    room = get_or_404(db, Room, room_id, "Room not found")
    db.delete(room)
    db.commit()