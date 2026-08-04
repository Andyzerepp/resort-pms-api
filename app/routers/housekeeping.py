from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_or_404
from app.models.models import Housekeeping, Room, User
from app.schemas.housekeeping import HousekeepingUpdate, HousekeepingResponse, HousekeepingIssueReport
from app.core.auth import require_role, get_current_user

router = APIRouter(
    prefix="/housekeeping",
    tags=["Housekeeping"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[HousekeepingResponse])
def get_housekeeping(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk", "housekeeping"))
):
    return db.query(Housekeeping).filter(
        Housekeeping.status.notin_(["inspected", "clean"])
    ).order_by(
        Housekeeping.priority.desc(),
        Housekeeping.created_at.asc()
    ).all()


@router.get("/room/{room_id}", response_model=HousekeepingResponse)
def get_room_housekeeping(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk", "housekeeping"))
):
    hk = db.query(Housekeeping).filter(
        Housekeeping.room_id == room_id
    ).order_by(Housekeeping.created_at.desc()).first()
    if not hk:
        raise HTTPException(status_code=404, detail="No housekeeping record found for this room")
    return hk


@router.get("/history", response_model=List[HousekeepingResponse])
def get_housekeeping_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk", "housekeeping"))
):
    return db.query(Housekeeping).filter(
        Housekeeping.status.in_(["inspected", "clean"])
    ).order_by(Housekeeping.completed_at.desc()).all()


@router.patch("/{task_id}/start", response_model=HousekeepingResponse)
def start_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "housekeeping"))
):
    hk = get_or_404(db, Housekeeping, task_id, "Task not found")
    if hk.status != "dirty":
        raise HTTPException(status_code=400, detail=f"Cannot start — task is currently '{hk.status}'")
    hk.status = "cleaning"
    hk.started_at = datetime.now(timezone.utc)
    hk.assigned_to = current_user.username
    db.commit()
    db.refresh(hk)
    return hk


@router.patch("/{task_id}/complete", response_model=HousekeepingResponse)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "housekeeping"))
):
    hk = get_or_404(db, Housekeeping, task_id, "Task not found")
    if hk.task_type == "pre_checkout_inspection":
        raise HTTPException(status_code=400, detail="Use clear-inspection or report-issue for inspections")
    if hk.status != "cleaning":
        raise HTTPException(status_code=400, detail=f"Cannot complete — task is currently '{hk.status}'")

    hk.status = "clean"
    hk.completed_at = datetime.now(timezone.utc)

    if hk.task_type in ["post_checkout_clean", "day_tour_turnover", "stayover_clean"]:
        room = db.query(Room).filter(Room.id == hk.room_id).first()
        if room:
            room.status = "available"

    db.commit()
    db.refresh(hk)
    return hk


@router.patch("/{task_id}/clear-inspection", response_model=HousekeepingResponse)
def clear_inspection(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "housekeeping"))
):
    hk = get_or_404(db, Housekeeping, task_id, "Task not found")
    if hk.task_type != "pre_checkout_inspection":
        raise HTTPException(status_code=400, detail="This action is only for pre-checkout inspections")
    if hk.status != "cleaning":
        raise HTTPException(status_code=400, detail="Inspection must be started first")

    hk.status = "inspected"
    hk.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(hk)
    return hk


@router.patch("/{task_id}/report-issue", response_model=HousekeepingResponse)
def report_issue(
    task_id: str,
    data: HousekeepingIssueReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "housekeeping"))
):
    hk = get_or_404(db, Housekeeping, task_id, "Task not found")
    if hk.task_type != "pre_checkout_inspection":
        raise HTTPException(status_code=400, detail="This action is only for pre-checkout inspections")
    if hk.status != "cleaning":
        raise HTTPException(status_code=400, detail="Inspection must be started first")

    hk.status = "room_flagged"
    hk.issue_found = True
    hk.notes = data.notes
    hk.issue_photo_path = data.issue_photo_path
    hk.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(hk)
    return hk


class ResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None

@router.patch("/{task_id}/resolve-issue", response_model=HousekeepingResponse)
def resolve_issue(
    task_id: str,
    data: ResolveRequest = ResolveRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "front_desk"))
):
    hk = get_or_404(db, Housekeeping, task_id, "Task not found")
    if hk.status != "room_flagged":
        raise HTTPException(status_code=400, detail="No open flag on this task")

    hk.status = "inspected"
    hk.resolved_by = current_user.username
    hk.resolved_at = datetime.now(timezone.utc)
    hk.resolution_notes = data.resolution_notes
    db.commit()
    db.refresh(hk)

    return hk


@router.patch("/room/{room_id}", response_model=HousekeepingResponse)
def update_housekeeping(
    room_id: str,
    data: HousekeepingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "housekeeping"))
):
    room = get_or_404(db, Room, room_id, "Room not found")

    hk = db.query(Housekeeping).filter(
        Housekeeping.room_id == room_id
    ).order_by(Housekeeping.created_at.desc()).first()

    if not hk:
        raise HTTPException(status_code=404, detail="No housekeeping record found for this room")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(hk, field, value)

    if data.status == "clean":
        room.status = "available"

    db.commit()
    db.refresh(hk)
    return hk