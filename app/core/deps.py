import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Type, TypeVar

ModelType = TypeVar("ModelType")


def get_or_404(db: Session, model: Type[ModelType], id: str, detail: str = None) -> ModelType:
    obj = db.query(model).filter(model.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=detail or f"{model.__name__} not found")
    return obj


TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def validate_time_string(value: str, field_name: str = "Time") -> str:
    if not TIME_RE.match(value):
        raise HTTPException(status_code=400, detail=f"{field_name} must be in HH:MM 24-hour format")
    return value