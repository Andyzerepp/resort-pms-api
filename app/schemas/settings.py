from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ResortSettingsResponse(BaseModel):
    id: str
    resort_name: str
    address: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    tin: Optional[str] = None
    default_checkin_time: str
    default_checkout_time: str
    early_checkin_fee: Decimal
    late_checkout_fee: Decimal
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class ResortSettingsUpdate(BaseModel):
    resort_name: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    tin: Optional[str] = None
    default_checkin_time: Optional[str] = None
    default_checkout_time: Optional[str] = None
    early_checkin_fee: Optional[Decimal] = None
    late_checkout_fee: Optional[Decimal] = None
