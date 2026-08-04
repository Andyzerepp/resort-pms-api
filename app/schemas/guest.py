from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GuestBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class GuestResponse(GuestBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True