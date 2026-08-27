"""initial schema

Revision ID: 20260827_0001
Revises:
Create Date: 2026-08-27
"""

from alembic import op

import app.db.models  # noqa: F401
from app.db.database import Base


revision = "20260827_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    for table in Base.metadata.sorted_tables:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(Base.metadata.sorted_tables):
        table.drop(bind=bind, checkfirst=True)

