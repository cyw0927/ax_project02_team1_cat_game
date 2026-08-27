import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RankingGroup(Base):
    __tablename__ = "ranking_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )


class RankingParticipant(Base):
    __tablename__ = "ranking_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ranking_groups.id"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    current_rank_score: Mapped[int] = mapped_column(Integer)


class RankChallenge(Base):
    __tablename__ = "rank_challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ranking_groups.id"),
    )
    status: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RankChallengeTask(Base):
    __tablename__ = "rank_challenge_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rank_challenges.id"),
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id"),
    )
    is_passed: Mapped[bool] = mapped_column(Boolean)
    saved_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_order: Mapped[int] = mapped_column(Integer)
