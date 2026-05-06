"""ServiceExtra — optional add-ons that customers can select when booking."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import BookingExtra
    from app.models.service import Service


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ServiceExtra(Base):
    __tablename__ = "service_extras"

    def __str__(self) -> str:
        return self.name

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(
        sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    default_selected: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )

    service: Mapped[Service] = relationship(back_populates="extras")
    booking_extras: Mapped[list[BookingExtra]] = relationship(back_populates="extra")
