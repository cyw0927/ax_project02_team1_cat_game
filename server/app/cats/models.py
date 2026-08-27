import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    persona: Mapped[str] = mapped_column(String)
    rarity: Mapped[str] = mapped_column(String)


class UserCat(Base):
    __tablename__ = "user_cats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
    )
    cat_id: Mapped[int] = mapped_column(
        ForeignKey("cats.id"),
    )


class CatMemory(Base):
    __tablename__ = "cat_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_cat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_cats.id"),
    )
    context_summary: Mapped[str] = mapped_column(Text)
