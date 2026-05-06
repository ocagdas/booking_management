from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import service_resources, service_staff
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.business import Business
    from app.models.resource import Resource
    from app.models.service_extra import ServiceExtra
    from app.models.staff import Staff


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalMode(str, enum.Enum):
    auto = "auto"
    manual = "manual"
    hybrid = "hybrid"


class PriceUnit(str, enum.Enum):
    flat = "flat"
    per_minute = "per_minute"
    per_5_min = "per_5_min"
    per_15_min = "per_15_min"
    per_30_min = "per_30_min"
    per_hour = "per_hour"


_PRICE_UNIT_MINUTES: dict[PriceUnit, int] = {
    PriceUnit.per_minute: 1,
    PriceUnit.per_5_min: 5,
    PriceUnit.per_15_min: 15,
    PriceUnit.per_30_min: 30,
    PriceUnit.per_hour: 60,
}

PRICE_UNIT_LABELS: dict[PriceUnit, str] = {
    PriceUnit.flat: "Flat fee (per booking)",
    PriceUnit.per_minute: "Per minute",
    PriceUnit.per_5_min: "Per 5 minutes",
    PriceUnit.per_15_min: "Per 15 minutes",
    PriceUnit.per_30_min: "Per 30 minutes",
    PriceUnit.per_hour: "Per hour",
}


def calculate_amount_due(
    unit_price: Decimal, price_unit: PriceUnit, duration_minutes: int
) -> Decimal:
    """Return the total amount due for a booking.

    For flat-fee services the unit_price is returned unchanged.  For
    time-based pricing the rate is multiplied by the number of billing
    units that fit in *duration_minutes*.
    """
    from decimal import ROUND_HALF_UP

    # Coerce to Decimal to handle int/float passed during tests or from forms.
    unit_price = Decimal(str(unit_price))

    if price_unit == PriceUnit.flat:
        return unit_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    unit_mins = Decimal(str(_PRICE_UNIT_MINUTES[price_unit]))
    units = Decimal(str(duration_minutes)) / unit_mins
    return (unit_price * units).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
    buffer_after_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    price_unit: Mapped[PriceUnit] = mapped_column(
        sa.Enum(PriceUnit, name="price_unit"),
        nullable=False,
        default=PriceUnit.flat,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        sa.Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    notes_prompt: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
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
    extras: Mapped[list[ServiceExtra]] = relationship(
        back_populates="service", order_by="ServiceExtra.sort_order"
    )
    resources: Mapped[list[Resource]] = relationship(
        secondary=service_resources, back_populates="services"
    )
    staff_members: Mapped[list[Staff]] = relationship(
        secondary=service_staff, back_populates="services"
    )
