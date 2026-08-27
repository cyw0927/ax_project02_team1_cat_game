import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.housing.models import PlacedObject
from app.users.models import User

router = APIRouter(tags=["housing"])

SURFACE_CATEGORIES = {"wallpaper", "floor"}


class PlaceObjectRequest(BaseModel):
    item_id: int
    position_data: dict = Field(min_length=1)


class MoveObjectRequest(BaseModel):
    position_data: dict = Field(min_length=1)


class SetSurfaceRequest(BaseModel):
    item_id: int


def _get_owned_item(
    db: Session,
    user_id: uuid.UUID,
    item_id: int,
) -> tuple[Item, int]:
    row = db.execute(
        select(Item, Inventory.quantity)
        .join(Inventory, Inventory.item_id == Item.id)
        .where(
            Inventory.user_id == user_id,
            Inventory.item_id == item_id,
            Inventory.quantity > 0,
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item is not in user inventory",
        )
    return row


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


@router.post(
    "/users/{user_id}/house/objects",
    status_code=status.HTTP_201_CREATED,
)
def place_object(
    user_id: uuid.UUID,
    payload: PlaceObjectRequest,
    db: Session = Depends(get_db),
):
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    item, quantity = _get_owned_item(db, user_id, payload.item_id)
    if item.category in SURFACE_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wallpaper and floor items cannot be placed as objects",
        )

    placed_count = db.scalar(
        select(func.count(PlacedObject.id)).where(
            PlacedObject.user_id == user_id,
            PlacedObject.item_id == payload.item_id,
        )
    )
    if placed_count >= quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="All owned copies of this item are already placed",
        )

    placed_object = PlacedObject(
        user_id=user_id,
        item_id=payload.item_id,
        position_data=payload.position_data,
    )
    db.add(placed_object)
    db.commit()
    db.refresh(placed_object)
    return {
        "placed_object_id": placed_object.id,
        "item_id": placed_object.item_id,
        "position_data": placed_object.position_data,
    }


@router.patch("/users/{user_id}/house/objects/{placed_object_id}")
def move_object(
    user_id: uuid.UUID,
    placed_object_id: uuid.UUID,
    payload: MoveObjectRequest,
    db: Session = Depends(get_db),
):
    placed_object = db.scalar(
        select(PlacedObject).where(
            PlacedObject.id == placed_object_id,
            PlacedObject.user_id == user_id,
        )
    )
    if placed_object is None:
        raise HTTPException(status_code=404, detail="Placed object not found")

    placed_object.position_data = payload.position_data
    db.commit()
    db.refresh(placed_object)
    return {
        "placed_object_id": placed_object.id,
        "item_id": placed_object.item_id,
        "position_data": placed_object.position_data,
    }


@router.delete("/users/{user_id}/house/objects/{placed_object_id}")
def remove_object(
    user_id: uuid.UUID,
    placed_object_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    placed_object = db.scalar(
        select(PlacedObject).where(
            PlacedObject.id == placed_object_id,
            PlacedObject.user_id == user_id,
        )
    )
    if placed_object is None:
        raise HTTPException(status_code=404, detail="Placed object not found")

    db.delete(placed_object)
    db.commit()
    return {"placed_object_id": placed_object_id, "removed": True}


def _set_surface(
    db: Session,
    user_id: uuid.UUID,
    item_id: int,
    expected_category: str,
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    item, _ = _get_owned_item(db, user_id, item_id)
    if item.category != expected_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item category must be {expected_category}",
        )

    attribute = f"{expected_category}_item_id"
    setattr(user, attribute, item.id)
    db.commit()
    db.refresh(user)
    return {attribute: item.id}


@router.put("/users/{user_id}/house/wallpaper")
def set_wallpaper(
    user_id: uuid.UUID,
    payload: SetSurfaceRequest,
    db: Session = Depends(get_db),
):
    return _set_surface(db, user_id, payload.item_id, "wallpaper")


@router.put("/users/{user_id}/house/floor")
def set_floor(
    user_id: uuid.UUID,
    payload: SetSurfaceRequest,
    db: Session = Depends(get_db),
):
    return _set_surface(db, user_id, payload.item_id, "floor")
