"""add purchase idempotency

Revision ID: 20260831_0004
Revises: 20260831_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260831_0004"
down_revision: str | Sequence[str] | None = "20260831_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "inventories",
        sa.Column(
            "last_purchase_request_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_inventories_last_purchase_request_id",
        "inventories",
        ["last_purchase_request_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_inventories_last_purchase_request_id",
        "inventories",
        type_="unique",
    )
    op.drop_column("inventories", "last_purchase_request_id")
