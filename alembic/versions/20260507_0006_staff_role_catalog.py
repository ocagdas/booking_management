"""Replace per-staff role strings with a shared Role catalog.

Revision ID: 20260507_0006
Revises: 20260506_0005_service_pricing_and_extras
Create Date: 2026-05-07

Changes
-------
* Drop the old ``staff_roles`` table (id, staff_id, role string, created_at).
* Create ``roles`` table — shared role definitions scoped to a business.
* Create new ``staff_roles`` M2M association table (staff_id ↔ role_id).
"""

import sqlalchemy as sa
from alembic import op

revision = "20260507_0006"
down_revision = "20260506_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old per-staff role table.
    op.drop_table("staff_roles")

    # Shared role catalog (one row per role definition per business).
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "business_id",
            sa.Integer,
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # M2M association: staff member ↔ role.
    op.create_table(
        "staff_roles",
        sa.Column(
            "staff_id",
            sa.Integer,
            sa.ForeignKey("staff.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.Integer,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("staff_roles")
    op.drop_table("roles")

    # Restore the original per-staff role string table.
    op.create_table(
        "staff_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "staff_id",
            sa.Integer,
            sa.ForeignKey("staff.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
