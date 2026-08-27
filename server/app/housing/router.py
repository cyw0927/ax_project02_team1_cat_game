import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.economy.models import Item
from app.housing.models import PlacedObject
from app.users.models import User

router = APIRouter(tags=["housing"])


@router.get("/users/{user_id}/house")
def get_house(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    rows = db.execute(
        select(
            PlacedObject.id,
            Item.id,
            Item.category,
            Item.name,
            PlacedObject.position_data,
        )
        .join(Item, Item.id == PlacedObject.item_id)
        .where(PlacedObject.user_id == user_id)
        .order_by(PlacedObject.id)
    ).all()

    return {
        "house_level": user.house_level,
        "wallpaper_item_id": user.wallpaper_item_id,
        "floor_item_id": user.floor_item_id,
        "placed_objects": [
            {
                "placed_object_id": placed_object_id,
                "item_id": item_id,
                "category": category,
                "name": name,
                "position_data": position_data,
            }
            for placed_object_id, item_id, category, name, position_data in rows
        ],
    }
