"""Service pricing (price_unit / unit_price), notes_prompt, amount_due,
service-resource/staff M2M tables, service_extras, booking_extras.

Revision ID: 20260506_0005
Revises: 20260506_0004
Create Date: 2026-05-06 23:30:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260506_0005"
down_revision = "20260506_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Create price_unit enum type (PostgreSQL only)
    # ------------------------------------------------------------------
    price_unit_type = postgresql.ENUM(
        "flat",
        "per_minute",
        "per_5_min",
        "per_15_min",
        "per_30_min",
        "per_hour",
        name="price_unit",
        create_type=False,
    )
    op.execute(
        "CREATE TYPE price_unit AS ENUM "
        "('flat','per_minute','per_5_min','per_15_min','per_30_min','per_hour')"
    )

    # ------------------------------------------------------------------
    # services: drop price_pence, add price_unit / unit_price / notes_prompt
    # ------------------------------------------------------------------
    op.drop_column("services", "price_pence")

    op.add_column(
        "services",
        sa.Column(
            "price_unit",
            price_unit_type,
            nullable=False,
            server_default="flat",
        ),
    )
    op.add_column(
        "services",
        sa.Column(
            "unit_price",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
    )
    op.add_column(
        "services",
        sa.Column("notes_prompt", sa.String(500), nullable=True),
    )

    # ------------------------------------------------------------------
    # bookings: add amount_due
    # ------------------------------------------------------------------
    op.add_column(
        "bookings",
        sa.Column("amount_due", sa.Numeric(10, 2), nullable=True),
    )

    # ------------------------------------------------------------------
    # service_resources (M2M junction)
    # ------------------------------------------------------------------
    op.create_table(
        "service_resources",
        sa.Column(
            "service_id",
            sa.Integer,
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "resource_id",
            sa.Integer,
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ------------------------------------------------------------------
    # service_staff (M2M junction)
    # ------------------------------------------------------------------
    op.create_table(
        "service_staff",
        sa.Column(
            "service_id",
            sa.Integer,
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "staff_id",
            sa.Integer,
            sa.ForeignKey("staff.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ------------------------------------------------------------------
    # service_extras
    # ------------------------------------------------------------------
    op.create_table(
        "service_extras",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "service_id",
            sa.Integer,
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("default_selected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ------------------------------------------------------------------
    # booking_extras
    # ------------------------------------------------------------------
    op.create_table(
        "booking_extras",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "booking_id",
            sa.Integer,
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "service_extra_id",
            sa.Integer,
            sa.ForeignKey("service_extras.id"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("booking_extras")
    op.drop_table("service_extras")
    op.drop_table("service_staff")
    op.drop_table("service_resources")
    op.drop_column("bookings", "amount_due")
    op.drop_column("services", "notes_prompt")
    op.drop_column("services", "unit_price")
    op.drop_column("services", "price_unit")
    op.add_column(
        "services",
        sa.Column("price_pence", sa.Integer, nullable=False, server_default="0"),
    )
    op.execute("DROP TYPE price_unit")
