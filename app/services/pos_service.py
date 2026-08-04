from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import POSOrder, POSItem, Folio
from app.services.folio_service import post_charge


def create_order(db: Session, outlet: str, items: list, folio_id: str = None):
    """Create a POS order with items. Optionally link to a folio."""
    if folio_id:
        folio = db.query(Folio).filter(Folio.id == folio_id).first()
        if not folio:
            raise HTTPException(status_code=404, detail="Folio not found")
        if folio.status != "open":
            raise HTTPException(status_code=400, detail="Folio is already settled")

    # Calculate total
    total = sum(float(item.unit_price) * item.quantity for item in items)

    order = POSOrder(
        folio_id=folio_id,
        outlet=outlet,
        total=total,
        status="open"
    )
    db.add(order)
    db.flush()

    # Add items
    for item in items:
        pos_item = POSItem(
            order_id=order.id,
            item_name=item.item_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=float(item.unit_price) * item.quantity
        )
        db.add(pos_item)

    db.flush()
    return order


def post_order_to_folio(db: Session, order_id: str, folio_id: str):
    """Post a completed POS order to a guest's folio."""
    order = db.query(POSOrder).filter(POSOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "open":
        raise HTTPException(status_code=400, detail="Order is already posted or voided")

    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    if folio.status != "open":
        raise HTTPException(status_code=400, detail="Folio is already settled")

    # Post each item as a charge
    for item in order.items:
        post_charge(
            db=db,
            folio_id=folio_id,
            charge_type="food",
            description=f"{item.quantity}x {item.item_name}",
            amount=float(item.subtotal)
        )

    # Link order to folio and mark as served
    order.folio_id = folio_id
    order.status = "served"

    db.flush()
    return order


def void_order(db: Session, order_id: str):
    """Void an open POS order."""
    order = db.query(POSOrder).filter(POSOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "open":
        raise HTTPException(status_code=400, detail="Only open orders can be voided")

    order.status = "voided"
    db.flush()
    return order