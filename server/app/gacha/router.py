import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cats.models import Cat, UserCat
from app.core.exception_handlers import AppException
from app.core.schemas import ErrorResponse
from app.db.database import get_db
from app.economy.models import Inventory, Item
from app.gacha.policy import (
    CURRENCY,
    DUPLICATE_CAT_MILEAGE,
    REGULAR_POOL,
    SINGLE_PULL_COST,
    TEN_PULL_COST,
    TEN_PULL_COUNT,
    TEN_PULL_GUARANTEED_POOL,
    PrizeDefinition,
    choose_prize,
    cost_for_count,
)
from app.gacha.schemas import (
    GachaInfoResponse,
    GachaPoolEntryResponse,
    GachaPullRequest,
    GachaPullResponse,
    GachaResultEntryResponse,
)
from app.users.dependencies import ROLE_ADMIN, ROLE_USER, require_roles
from app.users.models import User


router = APIRouter(prefix="/gacha", tags=["gacha"])


def _pool_response() -> list[GachaPoolEntryResponse]:
    total_weight = sum(prize.weight for prize in REGULAR_POOL)
    return [
        GachaPoolEntryResponse(
            reward_type=prize.reward_type,
            target_id=prize.target_id,
            name=prize.name,
            rarity=prize.rarity,
            probability_percent=prize.weight / total_weight * 100,
        )
        for prize in REGULAR_POOL
    ]


@router.get(
    "",
    response_model=GachaInfoResponse,
    summary="가챠 비용과 확률 조회",
)
def get_gacha_info() -> GachaInfoResponse:
    return GachaInfoResponse(
        currency=CURRENCY,
        single_cost=SINGLE_PULL_COST,
        ten_cost=TEN_PULL_COST,
        ten_pull_guarantee="마지막 1회는 SR 이상 고양이 확정",
        duplicate_cat_mileage=DUPLICATE_CAT_MILEAGE,
        pool=_pool_response(),
    )


def _require_pool_row(db: Session, prize: PrizeDefinition) -> Cat | Item:
    model = Cat if prize.reward_type == "CAT" else Item
    row = db.get(model, prize.target_id)
    if row is None:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="GACHA_POOL_INVALID",
            message="가챠 보상 데이터가 올바르지 않습니다.",
        )
    return row


@router.post(
    "/pull",
    response_model=GachaPullResponse,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "유료 재화 부족",
        },
    },
    summary="가챠 1회 또는 10회 실행",
)
def pull_gacha(
    payload: GachaPullRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> GachaPullResponse:
    user = db.get(User, current_user.id, with_for_update=True)
    if user is None:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="CURRENT_USER_NOT_FOUND",
            message="현재 사용자를 찾을 수 없습니다.",
        )

    if (
        user.last_gacha_request_id == payload.request_id
        and user.last_gacha_response is not None
    ):
        replay = GachaPullResponse.model_validate(user.last_gacha_response)
        if replay.count != payload.count:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="GACHA_REQUEST_CONFLICT",
                message="이미 다른 가챠 요청에 사용된 요청 ID입니다.",
            )
        return replay.model_copy(update={"replayed": True})

    cost = cost_for_count(payload.count)
    if user.hard_balance < cost:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_HARD_BALANCE",
            message="유료 재화가 부족합니다.",
        )

    owned_cat_ids = set(
        db.scalars(
            select(UserCat.cat_id).where(UserCat.user_id == user.id)
        ).all()
    )
    inventories = {
        inventory.item_id: inventory
        for inventory in db.scalars(
            select(Inventory)
            .where(Inventory.user_id == user.id)
            .with_for_update()
        ).all()
    }

    prizes = [choose_prize(REGULAR_POOL) for _ in range(payload.count)]
    if payload.count == TEN_PULL_COUNT:
        prizes[-1] = choose_prize(TEN_PULL_GUARANTEED_POOL)

    user.hard_balance -= cost
    results: list[GachaResultEntryResponse] = []

    for draw_index, prize in enumerate(prizes, start=1):
        reward = _require_pool_row(db, prize)
        if prize.reward_type == "CAT":
            is_new = prize.target_id not in owned_cat_ids
            mileage_awarded = 0
            if is_new:
                db.add(UserCat(user_id=user.id, cat_id=prize.target_id))
                owned_cat_ids.add(prize.target_id)
            else:
                mileage_awarded = DUPLICATE_CAT_MILEAGE[prize.rarity]
                user.mileage += mileage_awarded
            results.append(
                GachaResultEntryResponse(
                    draw_index=draw_index,
                    reward_type="CAT",
                    target_id=prize.target_id,
                    name=reward.name,
                    rarity=prize.rarity,
                    is_new=is_new,
                    mileage_awarded=mileage_awarded,
                )
            )
            continue

        inventory = inventories.get(prize.target_id)
        is_new = inventory is None
        if inventory is None:
            inventory = Inventory(
                user_id=user.id,
                item_id=prize.target_id,
                quantity=0,
                last_purchase_request_id=None,
            )
            db.add(inventory)
            inventories[prize.target_id] = inventory
        inventory.quantity += 1
        results.append(
            GachaResultEntryResponse(
                draw_index=draw_index,
                reward_type="ITEM",
                target_id=prize.target_id,
                name=reward.name,
                rarity=prize.rarity,
                is_new=is_new,
                quantity=inventory.quantity,
            )
        )

    response = GachaPullResponse(
        request_id=payload.request_id,
        count=payload.count,
        cost=cost,
        current_hard_balance=user.hard_balance,
        current_mileage=user.mileage,
        results=results,
        replayed=False,
    )
    user.last_gacha_request_id = payload.request_id
    user.last_gacha_response = response.model_dump(mode="json")

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return response


@router.get(
    "/results/{request_id}",
    response_model=GachaPullResponse,
    summary="마지막 가챠 요청 결과 재조회",
)
def get_gacha_result(
    request_id: uuid.UUID,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
) -> GachaPullResponse:
    if (
        current_user.last_gacha_request_id != request_id
        or current_user.last_gacha_response is None
    ):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="GACHA_RESULT_NOT_FOUND",
            message="가챠 결과를 찾을 수 없습니다.",
        )
    return GachaPullResponse.model_validate(current_user.last_gacha_response)
