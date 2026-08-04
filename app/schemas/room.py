from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class RoomTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    capacity: int = 2
    base_rate: Decimal


class RoomTypeCreate(RoomTypeBase):
    pass


class RoomTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    base_rate: Optional[Decimal] = None


class RoomTypeResponse(RoomTypeBase):
    id: str

    class Config:
        from_attributes = True


class RoomBase(BaseModel):
    room_type_id: str
    room_number: str
    floor: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    room_type_id: Optional[str] = None
    room_number: Optional[str] = None
    floor: Optional[str] = None
    status: Optional[str] = None


class RoomResponse(RoomBase):
    id: str
    status: str
    room_type: RoomTypeResponse

    class Config:
        from_attributes = True