import uuid
from typing import Literal

from pydantic import ConfigDict, Field

from app.core.schemas import SchemaBase


class CreateRoomRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=100, pattern=r"^.*\S.*$")
    max_participants: Literal[2, 4, 6, 8]


class SetReadyRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    is_ready: bool


class RoomSummaryResponse(SchemaBase):
    id: uuid.UUID
    title: str
    host_user_id: uuid.UUID
    status: str
    max_participants: int
    participant_count: int = Field(ge=0)


class ParticipantResponse(SchemaBase):
    participant_id: uuid.UUID
    user_id: uuid.UUID
    username: str
    team_name: str
    current_score: int = Field(ge=0)
    is_ready: bool
    is_host: bool


class RoomTaskResponse(SchemaBase):
    room_task_id: uuid.UUID
    task_id: uuid.UUID
    task_order: int = Field(ge=1)
    title: str
    type: str
    difficulty: str
    description: str
    template_code: str


class RoomDetailResponse(RoomSummaryResponse):
    participants: list[ParticipantResponse]
    tasks: list[RoomTaskResponse]
    winning_team: str | None = None


class JoinRoomResponse(SchemaBase):
    participant: ParticipantResponse
    rejoined: bool


class ReadyResponse(SchemaBase):
    participant_id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID
    is_ready: bool


class RoomStatusResponse(SchemaBase):
    room_id: uuid.UUID
    status: str


class BattleStateResponse(SchemaBase):
    room_id: uuid.UUID
    status: str
    winning_team: str | None
    participants: list[ParticipantResponse]
