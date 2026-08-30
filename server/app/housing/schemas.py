import uuid

from pydantic import ConfigDict, Field

from app.core.schemas import SchemaBase


class PositionData(SchemaBase):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    rotation: float = Field(default=0, ge=-360, le=360)
    scale: float = Field(default=1, ge=0.25, le=3)


class PlaceObjectRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")

    item_id: int
    position_data: PositionData


class MoveObjectRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")

    position_data: PositionData


class SetSurfaceRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")

    item_id: int


class PlacedObjectResponse(SchemaBase):
    placed_object_id: uuid.UUID
    item_id: int
    category: str | None = None
    name: str | None = None
    position_data: PositionData


class HouseResponse(SchemaBase):
    user_id: uuid.UUID
    house_level: int = Field(ge=1)
    wallpaper_item_id: int | None
    floor_item_id: int | None
    placed_objects: list[PlacedObjectResponse]


class RemoveObjectResponse(SchemaBase):
    placed_object_id: uuid.UUID
    removed: bool


class SurfaceResponse(SchemaBase):
    surface: str
    item_id: int
