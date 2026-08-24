from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.schemas.guest import GuestResponse
from app.schemas.folio import FolioResponse


class ReservationRoomCreate(BaseModel):
    room_id: str
    rate_at_booking: Decimal


class ReservationRoomResponse(BaseModel):
    id: str
    room_id: str
    room_number: Optional[str] = None
    rate_at_booking: Decimal

    class Config:
        from_attributes = True


class DeviationInfo(BaseModel):
    direction: str  # "early" | "late"
    minutes: int


class ReservationBase(BaseModel):
    guest_id: str
    check_in: date
    check_out: date
    source: Optional[str] = "walk_in"


class ReservationCreate(ReservationBase):
    rooms: List[ReservationRoomCreate]


class ReservationUpdate(BaseModel):
    status: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    source: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancellation_notes: Optional[str] = None
    cancelled_by: Optional[str] = None


class ReservationResponse(ReservationBase):
    id: str
    status: str
    checkin_time: Optional[str] = None
    checkout_time: Optional[str] = None
    checkin_deviation: Optional[DeviationInfo] = None
    checkout_deviation: Optional[DeviationInfo] = None
    total_amount: Optional[Decimal] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checkout_requested_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancellation_notes: Optional[str] = None
    guest: GuestResponse
    reservation_rooms: List[ReservationRoomResponse] = []
    folio: Optional[FolioResponse] = None

    class Config:
        from_attributes = True