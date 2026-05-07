from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import resource_locations, staff_locations
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.customer import Customer
    from app.models.resource import Resource
    from app.models.service import Service
    from app.models.staff import Role, Staff


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Business(Base):
    __tablename__ = "businesses"

    def __str__(self) -> str:
        return self.name

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    theme: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    locations: Mapped[list[Location]] = relationship(back_populates="business")
    services: Mapped[list[Service]] = relationship(back_populates="business")
    staff: Mapped[list[Staff]] = relationship(back_populates="business")
    roles: Mapped[list[Role]] = relationship(back_populates="business")
    resources: Mapped[list[Resource]] = relationship(back_populates="business")
    customers: Mapped[list[Customer]] = relationship(back_populates="business")
    bookings: Mapped[list[Booking]] = relationship(back_populates="business")


class Location(Base):
    __tablename__ = "locations"

    def __str__(self) -> str:
        return self.name

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="locations", lazy="joined")
    bookings: Mapped[list[Booking]] = relationship(back_populates="location")
    staff_members: Mapped[list[Staff]] = relationship(
        secondary=staff_locations, back_populates="locations"
    )
    resources: Mapped[list[Resource]] = relationship(
        secondary=resource_locations, back_populates="locations"
    )
