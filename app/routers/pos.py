from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_or_404
from app.models.models import POSOrder, User
from app.schemas.pos import POSOrderCreate, POSOrderResponse
from app.services import pos_service
from app.core.auth import require_role, get_current_user

router = APIRouter(
    prefix="/pos",
    tags=["POS"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/orders", response_model=List[POSOrderResponse])
def get_orders(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return db.query(POSOrder).all()


@router.get("/orders/{order_id}", response_model=POSOrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    return get_or_404(db, POSOrder, order_id, "Order not found")


@router.post("/orders", response_model=POSOrderResponse, status_code=201)
def create_order(data: POSOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    order = pos_service.create_order(
        db=db,
        outlet=data.outlet,
        items=data.items,
        folio_id=data.folio_id
    )
    db.commit()
    db.refresh(order)
    return order


@router.patch("/orders/{order_id}/post-to-folio", response_model=POSOrderResponse)
def post_to_folio(order_id: str, folio_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "front_desk"))):
    order = pos_service.post_order_to_folio(db, order_id, folio_id)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/orders/{order_id}/void", response_model=POSOrderResponse)
def void_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    order = pos_service.void_order(db, order_id)
    db.commit()
    db.refresh(order)
    return order