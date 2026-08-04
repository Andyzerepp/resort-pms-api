from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class POSItemCreate(BaseModel):
    item_name: str
    quantity: int = 1
    unit_price: Decimal


class POSItemResponse(POSItemCreate):
    id: str
    order_id: str
    subtotal: Decimal

    class Config:
        from_attributes = True


class POSOrderCreate(BaseModel):
    folio_id: Optional[str] = None
    outlet: str
    items: List[POSItemCreate]


class POSOrderUpdate(BaseModel):
    status: Optional[str] = None
    folio_id: Optional[str] = None


class POSOrderResponse(BaseModel):
    id: str
    folio_id: Optional[str] = None
    outlet: str
    status: str
    total: Decimal
    ordered_at: datetime
    items: List[POSItemResponse] = []

    class Config:
        from_attributes = True