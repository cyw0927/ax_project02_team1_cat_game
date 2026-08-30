import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "external_student_id",
            name="uq_users_external_student_id",
        ),
        CheckConstraint(
            "soft_balance >= 0",
            name="ck_users_soft_balance_nonnegative",
        ),
        CheckConstraint(
            "hard_balance >= 0",
            name="ck_users_hard_balance_nonnegative",
        ),
        CheckConstraint(
            "mileage >= 0",
            name="ck_users_mileage_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_student_id: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    soft_balance: Mapped[int] = mapped_column(Integer)
    hard_balance: Mapped[int] = mapped_column(Integer)
    mileage: Mapped[int] = mapped_column(Integer)
    house_level: Mapped[int] = mapped_column(Integer)

    wallpaper_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("items.id"),
        nullable=True,
    )
    floor_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("items.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "check_in_date",
            name="uq_attendances_user_date",
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
    check_in_date: Mapped[date] = mapped_column(Date)
    streak_count: Mapped[int] = mapped_column(Integer)
    daily_quest_completed: Mapped[bool] = mapped_column(Boolean)