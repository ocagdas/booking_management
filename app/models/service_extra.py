"""ServiceExtra — optional add-ons that customers can select when booking."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import staff_extras
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import BookingExtra
    from app.models.service import Service
    from app.models.staff import Staff


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
    # Pricing — same PriceUnit enum as Service.
    unit_price: Mapped[Decimal] = mapped_column(
        sa.Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    price_unit: Mapped[str] = mapped_column(
        sa.Enum("flat", "per_minute", "per_5_min", "per_15_min", "per_30_min", "per_hour",
                name="price_unit"),
        nullable=False,
        default="flat",
    )
    # Minimum duration in minutes (only meaningful for time-based price_unit).
    # None means no minimum beyond 1 unit of the price_unit.
    min_duration_minutes: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )

    service: Mapped[Service] = relationship(back_populates="extras")
    booking_extras: Mapped[list[BookingExtra]] = relationship(back_populates="extra")
    # Staff members explicitly permitted to offer this extra.
    # Empty → all staff who perform the parent service can offer it.
    staff_members: Mapped[list[Staff]] = relationship(
        secondary=staff_extras, back_populates="extras"
    )
