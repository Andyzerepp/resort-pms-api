from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_or_404
from app.models.models import Guest, User
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse
from app.core.auth import require_role, get_current_user

router = APIRouter(
    prefix="/guests",
    tags=["Guests"],
    dependencies=[Depends(get_current_user)],  # every route requires login by default
)


@router.get("/", response_model=List[GuestResponse])
def get_guests(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return db.query(Guest).all()


@router.get("/{guest_id}", response_model=GuestResponse)
def get_guest(guest_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return get_or_404(db, Guest, guest_id)


@router.post("/", response_model=GuestResponse, status_code=201)
def create_guest(data: GuestCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    guest = Guest(**data.model_dump())
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


@router.patch("/{guest_id}", response_model=GuestResponse)
def update_guest(guest_id: str, data: GuestUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    guest = get_or_404(db, Guest, guest_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(guest, field, value)
    db.commit()
    db.refresh(guest)
    return guest


@router.delete("/{guest_id}", status_code=204)
def delete_guest(guest_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    guest = get_or_404(db, Guest, guest_id)
    db.delete(guest)
    db.commit()