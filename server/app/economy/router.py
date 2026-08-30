import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handlers import AppException
from app.core.schemas import ErrorResponse
from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.economy.schemas import (
    BuyItemRequest,
    BuyItemResponse,
    InventoryItemResponse,
    ItemResponse,
)
from app.users.dependencies import ROLE_ADMIN, ROLE_USER, require_roles
from app.users.models import User


router = APIRouter(tags=["economy"])


@router.get(
    "/items",
    response_model=list[ItemResponse],
    summary="상점 상품 목록 조회",
)
def get_items(db: Session = Depends(get_db)) -> list[ItemResponse]:
    items = db.scalars(select(Item).order_by(Item.id)).all()
    return [ItemResponse.model_validate(item) for item in items]


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "상품을 찾을 수 없음",
        },
    },
    summary="상점 상품 상세 조회",
)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemResponse:
    item = db.get(Item, item_id)
    if item is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ITEM_NOT_FOUND",
            message="상품을 찾을 수 없습니다.",
        )
    return ItemResponse.model_validate(item)


@router.post(
    "/shop/buy",
    response_model=BuyItemResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "상품을 찾을 수 없음",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "잔액 부족 또는 idempotency key 충돌",
        },
    },
    summary="상점 상품 구매",
)
def buy_item(
    payload: BuyItemRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> BuyItemResponse:
    user = db.get(User, current_user.id, with_for_update=True)
    if user is None:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="CURRENT_USER_NOT_FOUND",
            message="현재 사용자를 찾을 수 없습니다.",
        )

    item = db.get(Item, payload.item_id)
    if item is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ITEM_NOT_FOUND",
            message="상품을 찾을 수 없습니다.",
        )

    replayed_purchase = db.scalar(
        select(Inventory).where(
            Inventory.last_purchase_request_id == payload.purchase_request_id
        )
    )
    if replayed_purchase is not None:
        if (
            replayed_purchase.user_id != user.id
            or replayed_purchase.item_id != item.id
        ):
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="PURCHASE_REQUEST_CONFLICT",
                message="이미 다른 구매에 사용된 요청 ID입니다.",
            )
        return BuyItemResponse(
            status="success",
            current_soft_balance=user.soft_balance,
            item_id=item.id,
            item_name=item.name,
            quantity=replayed_purchase.quantity,
            replayed=True,
        )

    if user.soft_balance < item.price:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_SOFT_BALANCE",
            message="일반 재화가 부족합니다.",
        )

    inventory = db.scalar(
        select(Inventory)
        .where(
            Inventory.user_id == user.id,
            Inventory.item_id == item.id,
        )
        .with_for_update()
    )
    if inventory is None:
        inventory = Inventory(
            id=uuid.uuid4(),
            user_id=user.id,
            item_id=item.id,
            quantity=0,
            last_purchase_request_id=None,
        )
        db.add(inventory)

    user.soft_balance -= item.price
    inventory.quantity += 1
    inventory.last_purchase_request_id = payload.purchase_request_id

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return BuyItemResponse(
        status="success",
        current_soft_balance=user.soft_balance,
        item_id=item.id,
        item_name=item.name,
        quantity=inventory.quantity,
        replayed=False,
    )


@router.get(
    "/users/{user_id}/inventory",
    response_model=list[InventoryItemResponse],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "다른 사용자의 인벤토리 접근",
        },
    },
    summary="현재 사용자의 보유 아이템 조회",
)
def get_inventory(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> list[InventoryItemResponse]:
    if user_id != current_user.id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_ACCESS_DENIED",
            message="다른 사용자의 인벤토리를 조회할 수 없습니다.",
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
        InventoryItemResponse(
            item_id=item_id,
            category=category,
            name=name,
            price=price,
            quantity=quantity,
        )
        for item_id, category, name, price, quantity in rows
    ]
