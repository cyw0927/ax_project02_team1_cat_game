"""add daily task snapshot

Revision ID: 20260831_0003
Revises: 3c63b197cf85
Create Date: 2026-08-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260831_0003"
down_revision: Union[str, Sequence[str], None] = "3c63b197cf85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "attendances",
        sa.Column(
            "daily_task_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_attendances_daily_task_ids_array",
        "attendances",
        "jsonb_typeof(daily_task_ids) = 'array'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_attendances_daily_task_ids_array",
        "attendances",
        type_="check",
    )
    op.drop_column("attendances", "daily_task_ids")
