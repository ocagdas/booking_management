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

# Staff ↔ Locations: a staff member can be assigned to multiple locations.
staff_locations = sa.Table(
    "staff_locations",
    Base.metadata,
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

# Resources ↔ Locations: a resource can be assigned to multiple locations.
resource_locations = sa.Table(
    "resource_locations",
    Base.metadata,
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

# Staff ↔ ServiceExtras: which extras a staff member can offer.
# Semantics: if a staff member has *any* row here for extras belonging to a
# service, only those extras are offered.  If no rows exist for any extras of
# that service, the staff member can offer *all* extras (default-all).
staff_extras = sa.Table(
    "staff_extras",
    Base.metadata,
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

# Staff ↔ Roles: many-to-many — a staff member can hold multiple roles.
staff_roles = sa.Table(
    "staff_roles",
    Base.metadata,
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
