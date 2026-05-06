"""add buffer_after_minutes to services

Revision ID: 20260506_0003
Revises: 20260506_0002
Create Date: 2026-05-06 23:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260506_0003"
down_revision = "20260506_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "services",
        sa.Column(
            "buffer_after_minutes",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("services", "buffer_after_minutes")
