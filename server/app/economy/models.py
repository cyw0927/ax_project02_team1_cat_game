import uuid

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    category: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)


class Inventory(Base):
    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "item_id",
            name="uq_inventories_user_item",
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
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id"),
    )
    quantity: Mapped[int] = mapped_column(Integer)