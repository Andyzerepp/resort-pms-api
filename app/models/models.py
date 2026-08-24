import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime,
    ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Guest(Base):
    __tablename__ = "guests"

    id                = Column(String, primary_key=True, default=gen_uuid)
    full_name         = Column(String(100), nullable=False)
    email             = Column(String(100), nullable=True)
    phone             = Column(String(30), nullable=True)
    address           = Column(Text, nullable=True)
    nationality       = Column(String(50), nullable=True)
    id_type           = Column(String(50), nullable=True)
    id_number         = Column(String(50), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    created_at        = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reservations = relationship("Reservation", back_populates="guest")


class RoomType(Base):
    __tablename__ = "room_types"
    id          = Column(String, primary_key=True, default=gen_uuid)
    name        = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    capacity    = Column(Integer, nullable=False, default=2)
    base_rate   = Column(Numeric(10, 2), nullable=False)
    rooms       = relationship("Room", back_populates="room_type")


class Room(Base):
    __tablename__ = "rooms"
    id           = Column(String, primary_key=True, default=gen_uuid)
    room_type_id = Column(String, ForeignKey("room_types.id"), nullable=False)
    room_number  = Column(String(20), unique=True, nullable=False)
    status       = Column(String(30), default="available")
    floor        = Column(String(20), nullable=True)
    room_type         = relationship("RoomType", back_populates="rooms")
    reservation_rooms = relationship("ReservationRoom", back_populates="room")
    housekeeping_logs = relationship("Housekeeping", back_populates="room")


class Reservation(Base):
    __tablename__ = "reservations"

    id                    = Column(String, primary_key=True, default=gen_uuid)
    guest_id              = Column(String, ForeignKey("guests.id"), nullable=False)
    status                = Column(String(30), default="confirmed")
    # status: confirmed | checked_in | checkout_requested | checked_out | cancelled
    check_in              = Column(Date, nullable=False)
    check_out             = Column(Date, nullable=False)
    checkin_time          = Column(String(5), nullable=True)   # e.g. "14:00"
    checkout_time         = Column(String(5), nullable=True)   # e.g. "12:00"
    total_amount          = Column(Numeric(12, 2), nullable=True)
    source                = Column(String(50), default="walk_in")
    booking_reference     = Column(String(20), nullable=True, unique=True)
    guest_count           = Column(Integer, default=1)
    special_requests      = Column(Text, nullable=True)
    created_by            = Column(String(100), nullable=True)
    checked_in_by         = Column(String(100), nullable=True)
    checked_out_by        = Column(String(100), nullable=True)
    created_at            = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    confirmed_at          = Column(DateTime, nullable=True)
    checked_in_at         = Column(DateTime, nullable=True)
    checkout_requested_at = Column(DateTime, nullable=True)
    checked_out_at        = Column(DateTime, nullable=True)
    cancelled_at          = Column(DateTime, nullable=True)
    cancelled_by          = Column(String(100), nullable=True)
    cancellation_reason   = Column(String(100), nullable=True)
    cancellation_notes    = Column(Text, nullable=True)

    guest             = relationship("Guest", back_populates="reservations")
    reservation_rooms = relationship("ReservationRoom", back_populates="reservation")
    folio             = relationship("Folio", back_populates="reservation", uselist=False)

    @property
    def checkin_deviation(self):
        from app.services.reservation_service import get_checkin_deviation
        return get_checkin_deviation(self)

    @property
    def checkout_deviation(self):
        from app.services.reservation_service import get_checkout_deviation
        return get_checkout_deviation(self)

class ReservationRoom(Base):
    __tablename__ = "reservation_rooms"
    id              = Column(String, primary_key=True, default=gen_uuid)
    reservation_id  = Column(String, ForeignKey("reservations.id"), nullable=False)
    room_id         = Column(String, ForeignKey("rooms.id"), nullable=False)
    rate_at_booking = Column(Numeric(10, 2), nullable=False)
    reservation = relationship("Reservation", back_populates="reservation_rooms")
    room        = relationship("Room", back_populates="reservation_rooms")

    @property
    def room_number(self):
        return self.room.room_number


class Folio(Base):
    __tablename__ = "folios"

    id              = Column(String, primary_key=True, default=gen_uuid)
    reservation_id  = Column(String, ForeignKey("reservations.id"), nullable=False)
    status          = Column(String(20), default="open")
    total_charges   = Column(Numeric(12, 2), default=0)
    total_payments  = Column(Numeric(12, 2), default=0)
    balance         = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    vat_amount      = Column(Numeric(12, 2), default=0)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    reservation = relationship("Reservation", back_populates="folio")
    charges     = relationship("FolioCharge", back_populates="folio")
    payments    = relationship("Payment", back_populates="folio")
    pos_orders  = relationship("POSOrder", back_populates="folio")


class FolioCharge(Base):
    __tablename__ = "folio_charges"

    id          = Column(String, primary_key=True, default=gen_uuid)
    folio_id    = Column(String, ForeignKey("folios.id"), nullable=False)
    charge_type = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    amount      = Column(Numeric(10, 2), nullable=False)
    posted_by   = Column(String(100), nullable=True)
    voided      = Column(Boolean, default=False)
    voided_by   = Column(String(100), nullable=True)
    voided_at   = Column(DateTime, nullable=True)
    charged_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    folio = relationship("Folio", back_populates="charges")


class Payment(Base):
    __tablename__ = "payments"

    id              = Column(String, primary_key=True, default=gen_uuid)
    folio_id        = Column(String, ForeignKey("folios.id"), nullable=False)
    method          = Column(String(30), nullable=False)
    amount          = Column(Numeric(10, 2), nullable=False)
    amount_tendered = Column(Numeric(10, 2), nullable=True)
    change_given    = Column(Numeric(10, 2), nullable=True)
    reference_no    = Column(String(100), nullable=True)
    received_by     = Column(String(100), nullable=True)
    paid_at         = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    folio = relationship("Folio", back_populates="payments")


class POSOrder(Base):
    __tablename__ = "pos_orders"
    id         = Column(String, primary_key=True, default=gen_uuid)
    folio_id   = Column(String, ForeignKey("folios.id"), nullable=True)
    outlet     = Column(String(50), nullable=False)
    status     = Column(String(30), default="open")
    total      = Column(Numeric(10, 2), default=0)
    ordered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    folio = relationship("Folio", back_populates="pos_orders")
    items = relationship("POSItem", back_populates="order")


class POSItem(Base):
    __tablename__ = "pos_items"
    id         = Column(String, primary_key=True, default=gen_uuid)
    order_id   = Column(String, ForeignKey("pos_orders.id"), nullable=False)
    item_name  = Column(String(150), nullable=False)
    quantity   = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal   = Column(Numeric(10, 2), nullable=False)
    order = relationship("POSOrder", back_populates="items")


class Housekeeping(Base):
    __tablename__ = "housekeeping"

    id            = Column(String, primary_key=True, default=gen_uuid)
    room_id       = Column(String, ForeignKey("rooms.id"), nullable=False)
    reservation_id = Column(String, ForeignKey("reservations.id"), nullable=True)
    task_type     = Column(String(30), default="post_checkout_clean")
    status        = Column(String(30), default="dirty")
    priority      = Column(String(20), default="normal")
    assigned_to   = Column(String(100), nullable=True)
    notes         = Column(Text, nullable=True)
    issue_found   = Column(Boolean, default=False)
    issue_photo_path = Column(String(255), nullable=True)
    resolved_by      = Column(String(100), nullable=True)
    resolved_at      = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at    = Column(DateTime, nullable=True)
    completed_at  = Column(DateTime, nullable=True)
    updated_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    room        = relationship("Room", back_populates="housekeeping_logs")
    reservation = relationship("Reservation", foreign_keys=[reservation_id])

class ResortSettings(Base):
    __tablename__ = "resort_settings"

    id                   = Column(String, primary_key=True, default=gen_uuid)
    resort_name          = Column(String(200), nullable=False, default="Anilao Highland Farm Resort, Inc.")
    address              = Column(Text, nullable=True)
    contact_number       = Column(String(50), nullable=True)
    email                = Column(String(100), nullable=True)
    tin                  = Column(String(50), nullable=True)
    default_checkin_time = Column(String(5), default="14:00")
    default_checkout_time = Column(String(5), default="12:00")
    early_checkin_fee    = Column(Numeric(10, 2), default=0)
    late_checkout_fee    = Column(Numeric(10, 2), default=0)
    updated_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by           = Column(String(100), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, nullable=True)
    username    = Column(String(100), nullable=True)
    action      = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id   = Column(String, nullable=True)
    details     = Column(Text, nullable=True)
    ip_address  = Column(String(50), nullable=True)
    timestamp   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    success     = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"

    id         = Column(String, primary_key=True, default=gen_uuid)
    username   = Column(String(50), unique=True, nullable=False)
    full_name  = Column(String(100), nullable=True)
    password   = Column(String(255), nullable=False)
    role       = Column(String(20), nullable=False, default="front_desk")
    is_active  = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))