import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id"),
    )
    title: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    difficulty: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    template_code: Mapped[str] = mapped_column(Text)
    test_cases: Mapped[str] = mapped_column(Text)
    hint_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean)


class UserProficiency(Base):
    __tablename__ = "user_proficiency"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "concept_id",
            name="uq_user_proficiency_user_concept",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id"),
    )
    proficiency_level: Mapped[int] = mapped_column(Integer)


class TaskAttempt(Base):
    __tablename__ = "task_attempts"
    __table_args__ = (
        CheckConstraint(
            """
            (
                context_type = 'LEARNING'
                AND attendance_id IS NULL
                AND room_task_id IS NULL
                AND rank_challenge_task_id IS NULL
            )
            OR
            (
                context_type = 'DAILY'
                AND attendance_id IS NOT NULL
                AND room_task_id IS NULL
                AND rank_challenge_task_id IS NULL
            )
            OR
            (
                context_type = 'BATTLE'
                AND attendance_id IS NULL
                AND room_task_id IS NOT NULL
                AND rank_challenge_task_id IS NULL
            )
            OR
            (
                context_type = 'RANKING'
                AND attendance_id IS NULL
                AND room_task_id IS NULL
                AND rank_challenge_task_id IS NOT NULL
            )
            """,
            name="ck_task_attempts_context",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id"),
    )

    context_type: Mapped[str] = mapped_column(String)

    attendance_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("attendances.id"),
        nullable=True,
    )
    room_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("room_tasks.id"),
        nullable=True,
    )
    rank_challenge_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rank_challenge_tasks.id"),
        nullable=True,
    )

    submitted_code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String)
    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    used_hint: Mapped[bool] = mapped_column(Boolean)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )