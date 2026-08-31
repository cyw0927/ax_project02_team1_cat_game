import uuid

from pydantic import ConfigDict, Field

from app.core.schemas import SchemaBase


class ItemResponse(SchemaBase):
    id: int
    category: str
    name: str
    price: int = Field(ge=0)


class BuyItemRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")

    item_id: int
    purchase_request_id: uuid.UUID


class BuyItemResponse(SchemaBase):
    status: str
    current_soft_balance: int = Field(ge=0)
    item_id: int
    item_name: str
    quantity: int = Field(ge=1)
    replayed: bool


class InventoryItemResponse(SchemaBase):
    item_id: int
    category: str
    name: str
    price: int = Field(ge=0)
    quantity: int = Field(ge=1)
