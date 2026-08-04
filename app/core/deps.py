from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Type, TypeVar

ModelType = TypeVar("ModelType")


def get_or_404(db: Session, model: Type[ModelType], id: str, detail: str = None) -> ModelType:
    obj = db.query(model).filter(model.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=detail or f"{model.__name__} not found")
    return obj