from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.business import Business


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalMode(str, enum.Enum):
    auto = "auto"
    manual = "manual"
    hybrid = "hybrid"


class Service(Base):
    __tablename__ = "services"

    def __str__(self) -> str:
        return self.name

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    price_pence: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    approval_mode: Mapped[ApprovalMode] = mapped_column(
        sa.Enum(ApprovalMode, name="approval_mode"),
        nullable=False,
        default=ApprovalMode.auto,
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="services")
    bookings: Mapped[list[Booking]] = relationship(back_populates="service")
