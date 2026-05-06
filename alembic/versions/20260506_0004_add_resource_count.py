"""add count to resources

Revision ID: 20260506_0004
Revises: 20260506_0003
Create Date: 2026-05-06 23:10:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260506_0004"
down_revision = "20260506_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resources",
        sa.Column("count", sa.Integer, nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("resources", "count")
