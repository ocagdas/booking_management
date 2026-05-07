from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import service_staff, staff_roles
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import BookingStaff
    from app.models.business import Business
    from app.models.service import Service


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Role(Base):
    """A named role that can be assigned to one or more staff members.

    Roles are defined at the business level so the same catalog is shared
    across all staff in the business (e.g. "Mechanic", "Receptionist",
    "Senior Technician").
    """

    __tablename__ = "roles"

    def __str__(self) -> str:
        return self.name

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="roles")
    staff_members: Mapped[list[Staff]] = relationship(
        secondary=staff_roles, back_populates="roles"
    )


class Staff(Base):
    __tablename__ = "staff"

    def __str__(self) -> str:
        return self.name

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="staff")
    roles: Mapped[list[Role]] = relationship(
        secondary=staff_roles, back_populates="staff_members"
    )
    booking_staff: Mapped[list[BookingStaff]] = relationship(back_populates="staff_member")
    services: Mapped[list[Service]] = relationship(
        secondary=service_staff, back_populates="staff_members"
    )
