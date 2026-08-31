import uuid
from typing import Literal

from pydantic import ConfigDict, Field

from app.core.schemas import SchemaBase


class GachaPullRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")

    count: Literal[1, 10]
    request_id: uuid.UUID


class GachaPoolEntryResponse(SchemaBase):
    reward_type: Literal["CAT", "ITEM"]
    target_id: int
    name: str
    rarity: str
    probability_percent: float = Field(gt=0, le=100)


class GachaInfoResponse(SchemaBase):
    currency: Literal["HARD"]
    single_cost: int = Field(ge=1)
    ten_cost: int = Field(ge=1)
    ten_pull_guarantee: str
    duplicate_cat_mileage: dict[str, int]
    pool: list[GachaPoolEntryResponse]


class GachaResultEntryResponse(SchemaBase):
    draw_index: int = Field(ge=1, le=10)
    reward_type: Literal["CAT", "ITEM"]
    target_id: int
    name: str
    rarity: str
    is_new: bool
    quantity: int | None = Field(default=None, ge=1)
    mileage_awarded: int = Field(default=0, ge=0)


class GachaPullResponse(SchemaBase):
    request_id: uuid.UUID
    count: Literal[1, 10]
    cost: int = Field(ge=1)
    current_hard_balance: int = Field(ge=0)
    current_mileage: int = Field(ge=0)
    results: list[GachaResultEntryResponse]
    replayed: bool
