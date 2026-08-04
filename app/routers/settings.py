from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import validate_time_string
from app.models.models import ResortSettings, User
from app.schemas.settings import ResortSettingsResponse, ResortSettingsUpdate
from app.core.auth import require_role, get_current_user

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(get_current_user)],
)


def _get_or_create_settings(db: Session) -> ResortSettings:
    settings = db.query(ResortSettings).first()
    if not settings:
        settings = ResortSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=ResortSettingsResponse)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return _get_or_create_settings(db)


@router.patch("", response_model=ResortSettingsResponse)
def update_settings(
    data: ResortSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    settings = _get_or_create_settings(db)
    updates = data.model_dump(exclude_unset=True)

    if "default_checkin_time" in updates and updates["default_checkin_time"] is not None:
        validate_time_string(updates["default_checkin_time"], "Default check-in time")
    if "default_checkout_time" in updates and updates["default_checkout_time"] is not None:
        validate_time_string(updates["default_checkout_time"], "Default check-out time")
    if updates.get("early_checkin_fee") is not None and updates["early_checkin_fee"] < 0:
        raise HTTPException(status_code=400, detail="Early check-in fee must be ₱0 or more")
    if updates.get("late_checkout_fee") is not None and updates["late_checkout_fee"] < 0:
        raise HTTPException(status_code=400, detail="Late check-out fee must be ₱0 or more")

    for field, value in updates.items():
        setattr(settings, field, value)
    settings.updated_by = current_user.username

    db.commit()
    db.refresh(settings)
    return settings
