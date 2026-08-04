from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HousekeepingUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class HousekeepingIssueReport(BaseModel):
    notes: str
    issue_photo_path: Optional[str] = None


class GuestSummary(BaseModel):
    full_name: str

    class Config:
        from_attributes = True


class ReservationSummary(BaseModel):
    id: str
    guest: GuestSummary

    class Config:
        from_attributes = True


class HousekeepingResponse(BaseModel):
    id: str
    room_id: str
    reservation_id: Optional[str] = None
    task_type: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    issue_found: bool
    issue_photo_path: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
    reservation: Optional[ReservationSummary] = None

    class Config:
        from_attributes = True