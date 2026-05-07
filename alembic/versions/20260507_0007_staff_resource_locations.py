"""Add staff_locations and resource_locations M2M tables.

Revision ID: 20260507_0007
Revises: 20260507_0006
Create Date: 2026-05-07

Changes
-------
* Create ``staff_locations`` M2M association table (staff_id ↔ location_id).
* Create ``resource_locations`` M2M association table (resource_id ↔ location_id).

These tables allow a staff member or resource to be assigned to multiple
locations.  Availability is enforced globally: if a staff member or resource
is booked at one location their booking blocks them at all other locations
for the same time window.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260507_0007"
down_revision = "20260507_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_locations",
        sa.Column(
            "staff_id",
            sa.Integer,
            sa.ForeignKey("staff.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "location_id",
            sa.Integer,
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "resource_locations",
        sa.Column(
            "resource_id",
            sa.Integer,
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "location_id",
            sa.Integer,
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("resource_locations")
    op.drop_table("staff_locations")
