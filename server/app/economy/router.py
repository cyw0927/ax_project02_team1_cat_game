from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.economy.models import Item

router = APIRouter(tags=["economy"])


@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    items = db.scalars(select(Item).order_by(Item.id)).all()

    return [
        {
            "id": item.id,
            "category": item.category,
            "name": item.name,
            "price": item.price,
        }
        for item in items
    ]
