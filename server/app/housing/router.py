import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exception_handlers import AppException
from app.core.schemas import ErrorResponse
from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.housing.models import PlacedObject
from app.housing.schemas import (
    HouseResponse,
    MoveObjectRequest,
    PlaceObjectRequest,
    PlacedObjectResponse,
    RemoveObjectResponse,
    SetSurfaceRequest,
    SurfaceResponse,
)
from app.users.dependencies import ROLE_ADMIN, ROLE_USER, require_roles
from app.users.models import User


router = APIRouter(tags=["housing"])

FURNITURE_CATEGORY = "FURNITURE"
WALLPAPER_CATEGORY = "WALLPAPER"
FLOOR_CATEGORY = "FLOOR"


def _require_path_owner(user_id: uuid.UUID, current_user: User) -> None:
    if user_id != current_user.id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_ACCESS_DENIED",
            message="다른 사용자의 하우징을 변경할 수 없습니다.",
        )


def _get_owned_item(
    db: Session,
    user_id: uuid.UUID,
    item_id: int,
) -> tuple[Item, Inventory]:
    row = db.execute(
        select(Item, Inventory)
        .join(Inventory, Inventory.item_id == Item.id)
        .where(
            Inventory.user_id == user_id,
            Inventory.item_id == item_id,
            Inventory.quantity > 0,
        )
        .with_for_update()
    ).one_or_none()
    if row is None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ITEM_NOT_OWNED",
            message="보유하지 않은 아이템입니다.",
        )
    return row


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


@router.get(
    "/users/{user_id}/house",
    response_model=HouseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "사용자를 찾을 수 없음",
        },
    },
    summary="사용자 하우징 조회",
)
def get_house(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> HouseResponse:
    user = db.get(User, user_id)
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
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

    return HouseResponse(
        user_id=user.id,
        house_level=user.house_level,
        wallpaper_item_id=user.wallpaper_item_id,
        floor_item_id=user.floor_item_id,
        placed_objects=[
            PlacedObjectResponse(
                placed_object_id=placed_object_id,
                item_id=item_id,
                category=category,
                name=name,
                position_data=position_data,
            )
            for placed_object_id, item_id, category, name, position_data in rows
        ],
    )


@router.post(
    "/users/{user_id}/house/objects",
    response_model=PlacedObjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="보유 가구 배치",
)
def place_object(
    user_id: uuid.UUID,
    payload: PlaceObjectRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> PlacedObjectResponse:
    _require_path_owner(user_id, current_user)
    item, inventory = _get_owned_item(db, user_id, payload.item_id)
    if item.category != FURNITURE_CATEGORY:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ITEM_NOT_PLACEABLE",
            message="가구 아이템만 배치할 수 있습니다.",
        )

    placed_count = db.scalar(
        select(func.count(PlacedObject.id)).where(
            PlacedObject.user_id == user_id,
            PlacedObject.item_id == payload.item_id,
        )
    )
    if placed_count >= inventory.quantity:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="PLACEMENT_QUANTITY_EXCEEDED",
            message="보유 수량을 초과하여 배치할 수 없습니다.",
        )

    placed_object = PlacedObject(
        user_id=user_id,
        item_id=payload.item_id,
        position_data=payload.position_data.model_dump(),
    )
    db.add(placed_object)
    _commit(db)
    db.refresh(placed_object)
    return PlacedObjectResponse(
        placed_object_id=placed_object.id,
        item_id=placed_object.item_id,
        category=item.category,
        name=item.name,
        position_data=placed_object.position_data,
    )


@router.patch(
    "/users/{user_id}/house/objects/{placed_object_id}",
    response_model=PlacedObjectResponse,
    summary="배치 가구 이동",
)
def move_object(
    user_id: uuid.UUID,
    placed_object_id: uuid.UUID,
    payload: MoveObjectRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> PlacedObjectResponse:
    _require_path_owner(user_id, current_user)
    placed_object = db.scalar(
        select(PlacedObject).where(
            PlacedObject.id == placed_object_id,
            PlacedObject.user_id == user_id,
        )
    )
    if placed_object is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PLACED_OBJECT_NOT_FOUND",
            message="배치된 가구를 찾을 수 없습니다.",
        )

    placed_object.position_data = payload.position_data.model_dump()
    _commit(db)
    db.refresh(placed_object)
    return PlacedObjectResponse(
        placed_object_id=placed_object.id,
        item_id=placed_object.item_id,
        position_data=placed_object.position_data,
    )


@router.delete(
    "/users/{user_id}/house/objects/{placed_object_id}",
    response_model=RemoveObjectResponse,
    summary="배치 가구 회수",
)
def remove_object(
    user_id: uuid.UUID,
    placed_object_id: uuid.UUID,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> RemoveObjectResponse:
    _require_path_owner(user_id, current_user)
    placed_object = db.scalar(
        select(PlacedObject).where(
            PlacedObject.id == placed_object_id,
            PlacedObject.user_id == user_id,
        )
    )
    if placed_object is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PLACED_OBJECT_NOT_FOUND",
            message="배치된 가구를 찾을 수 없습니다.",
        )

    db.delete(placed_object)
    _commit(db)
    return RemoveObjectResponse(
        placed_object_id=placed_object_id,
        removed=True,
    )


def _set_surface(
    db: Session,
    user: User,
    item_id: int,
    expected_category: str,
) -> SurfaceResponse:
    item, _ = _get_owned_item(db, user.id, item_id)
    if item.category != expected_category:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_SURFACE_CATEGORY",
            message=f"{expected_category} 아이템만 적용할 수 있습니다.",
        )

    attribute = (
        "wallpaper_item_id"
        if expected_category == WALLPAPER_CATEGORY
        else "floor_item_id"
    )
    setattr(user, attribute, item.id)
    _commit(db)
    return SurfaceResponse(surface=expected_category, item_id=item.id)


@router.put(
    "/users/{user_id}/house/wallpaper",
    response_model=SurfaceResponse,
    summary="벽지 적용",
)
def set_wallpaper(
    user_id: uuid.UUID,
    payload: SetSurfaceRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> SurfaceResponse:
    _require_path_owner(user_id, current_user)
    return _set_surface(db, current_user, payload.item_id, WALLPAPER_CATEGORY)


@router.put(
    "/users/{user_id}/house/floor",
    response_model=SurfaceResponse,
    summary="바닥 적용",
)
def set_floor(
    user_id: uuid.UUID,
    payload: SetSurfaceRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> SurfaceResponse:
    _require_path_owner(user_id, current_user)
    return _set_surface(db, current_user, payload.item_id, FLOOR_CATEGORY)
