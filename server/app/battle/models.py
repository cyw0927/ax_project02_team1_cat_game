import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String)
    host_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    status: Mapped[str] = mapped_column(String)
    max_participants: Mapped[int] = mapped_column(Integer)


class RoomParticipant(Base):
    __tablename__ = "room_participants"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_room_participants_room_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    team_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    current_score: Mapped[int] = mapped_column(Integer)
    is_ready: Mapped[bool] = mapped_column(Boolean)


class RoomTask(Base):
    __tablename__ = "room_tasks"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "task_id",
            name="uq_room_tasks_room_task",
        ),
        UniqueConstraint(
            "room_id",
            "task_order",
            name="uq_room_tasks_room_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id"),
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id"),
    )
    task_order: Mapped[int] = mapped_column(Integer)