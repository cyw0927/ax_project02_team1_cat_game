import secrets
from dataclasses import dataclass
from typing import Callable, Sequence


SINGLE_PULL_COUNT = 1
TEN_PULL_COUNT = 10
SINGLE_PULL_COST = 10
TEN_PULL_COST = 90
CURRENCY = "HARD"


@dataclass(frozen=True)
class PrizeDefinition:
    reward_type: str
    target_id: int
    name: str
    rarity: str
    weight: int


REGULAR_POOL = (
    PrizeDefinition("CAT", 1, "나비", "N", 40),
    PrizeDefinition("CAT", 2, "구름", "R", 25),
    PrizeDefinition("CAT", 3, "별이", "SR", 10),
    PrizeDefinition("CAT", 4, "루나", "SSR", 5),
    PrizeDefinition("ITEM", 1, "파란 별 벽지", "ITEM", 5),
    PrizeDefinition("ITEM", 2, "원목 바닥", "ITEM", 5),
    PrizeDefinition("ITEM", 3, "기본 캣타워", "ITEM", 5),
    PrizeDefinition("ITEM", 4, "학습용 책상", "ITEM", 5),
)

TEN_PULL_GUARANTEED_POOL = (
    PrizeDefinition("CAT", 3, "별이", "SR", 80),
    PrizeDefinition("CAT", 4, "루나", "SSR", 20),
)

DUPLICATE_CAT_MILEAGE = {
    "N": 5,
    "R": 10,
    "SR": 25,
    "SSR": 100,
}


def cost_for_count(count: int) -> int:
    if count == SINGLE_PULL_COUNT:
        return SINGLE_PULL_COST
    if count == TEN_PULL_COUNT:
        return TEN_PULL_COST
    raise ValueError("지원하지 않는 가챠 횟수입니다.")


def choose_prize(
    pool: Sequence[PrizeDefinition],
    randbelow: Callable[[int], int] = secrets.randbelow,
) -> PrizeDefinition:
    total_weight = sum(prize.weight for prize in pool)
    roll = randbelow(total_weight)
    cumulative = 0
    for prize in pool:
        cumulative += prize.weight
        if roll < cumulative:
            return prize
    raise RuntimeError("가챠 확률표가 올바르지 않습니다.")
