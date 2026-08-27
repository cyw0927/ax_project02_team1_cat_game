import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.users.models import User

router = APIRouter(tags=["economy"])


class BuyItemRequest(BaseModel):
    user_id: uuid.UUID
    item_id: int


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


@router.post("/shop/buy")
def buy_item(payload: BuyItemRequest, db: Session = Depends(get_db)):
    if db.get(User, payload.user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    item = db.get(Item, payload.item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    balance_result = db.execute(
        update(User)
        .where(
            User.id == payload.user_id,
            User.balance >= item.price,
        )
        .values(balance=User.balance - item.price)
        .returning(User.balance)
    )
    current_balance = balance_result.scalar_one_or_none()

    if current_balance is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insufficient balance",
        )

    inventory_statement = (
        insert(Inventory)
        .values(
            id=uuid.uuid4(),
            user_id=payload.user_id,
            item_id=item.id,
            quantity=1,
        )
        .on_conflict_do_update(
            index_elements=[Inventory.user_id, Inventory.item_id],
            set_={"quantity": Inventory.quantity + 1},
        )
        .returning(Inventory.quantity)
    )
    quantity = db.scalar(inventory_statement)

    db.commit()

    return {
        "status": "success",
        "current_balance": current_balance,
        "item_id": item.id,
        "item_name": item.name,
        "quantity": quantity,
    }


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
