from sqlalchemy import Column, ForeignKey, Table

from app.models.base import Base

service_locations = Table(
    "service_locations",
    Base.metadata,
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    Column("location_id", ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True),
)
