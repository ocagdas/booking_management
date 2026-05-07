"""Extra pricing fields, staff_extras M2M, services min_duration, location_id data fix.

Revision ID: 20260507_0008
Revises: 20260507_0007
Create Date: 2026-05-07

Changes
-------
* ``service_extras``: add ``unit_price``, ``price_unit``, ``min_duration_minutes``.
* ``services``: add ``min_duration_minutes`` (optional minimum booking length).
* Create ``staff_extras`` M2M table (staff_id ↔ service_extra_id).
  An entry means that staff member can offer that specific extra.
  If a staff member has *no* entries for any extra of a service they can
  offer *all* extras for that service (default-all semantics).
* Data migration: set ``bookings.location_id`` to the first location of
  the booking's business for every row where ``location_id IS NULL``.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260507_0008"
down_revision = "20260507_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # service_extras: pricing fields
    # ------------------------------------------------------------------
    # Reuse the existing price_unit enum type (already in the DB from 0005).
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

    op.add_column(
        "service_extras",
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    op.add_column(
        "service_extras",
        sa.Column("price_unit", price_unit_type, nullable=False, server_default="flat"),
    )
    op.add_column(
        "service_extras",
        sa.Column("min_duration_minutes", sa.Integer, nullable=True),
    )

    # ------------------------------------------------------------------
    # services: minimum booking duration
    # ------------------------------------------------------------------
    op.add_column(
        "services",
        sa.Column("min_duration_minutes", sa.Integer, nullable=True),
    )

    # ------------------------------------------------------------------
    # staff_extras M2M: which extras a staff member can offer
    # ------------------------------------------------------------------
    op.create_table(
        "staff_extras",
        sa.Column(
            "staff_id",
            sa.Integer,
            sa.ForeignKey("staff.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "service_extra_id",
            sa.Integer,
            sa.ForeignKey("service_extras.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ------------------------------------------------------------------
    # Data migration: fill NULL location_id with the business's first location
    # ------------------------------------------------------------------
    # Note: if a business has no locations at all, its bookings will remain
    # with location_id = NULL.  This is intentional — the column is nullable
    # and those bookings are unaffected until a location is created for that
    # business.
    op.execute(
        """
        UPDATE bookings
        SET location_id = (
            SELECT l.id
            FROM locations l
            WHERE l.business_id = bookings.business_id
            ORDER BY l.id
            LIMIT 1
        )
        WHERE location_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_table("staff_extras")
    op.drop_column("services", "min_duration_minutes")
    op.drop_column("service_extras", "min_duration_minutes")
    op.drop_column("service_extras", "price_unit")
    op.drop_column("service_extras", "unit_price")
