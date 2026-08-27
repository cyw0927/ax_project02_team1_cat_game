import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.users.models import User

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


@router.get("/users/{user_id}/inventory")
def get_inventory(user_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    rows = db.execute(
        select(
            Item.id,
            Item.category,
            Item.name,
            Item.price,
            Inventory.quantity,
        )
        .join(Inventory, Inventory.item_id == Item.id)
        .where(Inventory.user_id == user_id)
        .order_by(Item.id)
    ).all()

    return [
        {
            "item_id": item_id,
            "category": category,
            "name": name,
            "price": price,
            "quantity": quantity,
        }
        for item_id, category, name, price, quantity in rows
    ]
