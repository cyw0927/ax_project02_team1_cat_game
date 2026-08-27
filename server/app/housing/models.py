import uuid
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PlacedObject(Base):
    __tablename__ = "placed_objects"

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
    position_data: Mapped[dict[str, Any]] = mapped_column(JSONB)
