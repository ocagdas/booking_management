"""SQLAlchemy association (secondary) tables for many-to-many relationships.

These are plain Table objects (not mapped classes) so that both sides of
each relationship can import them without circular-import issues.
"""

import sqlalchemy as sa

from app.models.base import Base

# Services ↔ Resources: which resource types are available for a service.
service_resources = sa.Table(
    "service_resources",
    Base.metadata,
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

# Services ↔ Staff: which staff members can perform a service.
service_staff = sa.Table(
    "service_staff",
    Base.metadata,
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
