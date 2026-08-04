from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class FolioChargeCreate(BaseModel):
    charge_type: str
    description: Optional[str] = None
    amount: Decimal


class FolioChargeResponse(FolioChargeCreate):
    id: str
    folio_id: str
    posted_by: Optional[str] = None
    charged_at: datetime
    voided: bool = False
    voided_by: Optional[str] = None
    voided_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    method: str
    amount: Decimal
    amount_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    reference_no: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    folio_id: str
    method: str
    amount: Decimal
    amount_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    reference_no: Optional[str] = None
    received_by: Optional[str] = None
    paid_at: datetime

    class Config:
        from_attributes = True


class FolioResponse(BaseModel):
    id: str
    reservation_id: str
    total_charges: Decimal
    total_payments: Decimal
    balance: Decimal
    status: str
    charges: List[FolioChargeResponse] = []
    payments: List[PaymentResponse] = []

    class Config:
        from_attributes = True