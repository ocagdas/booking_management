from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.business import Business, Location
    from app.models.customer import Customer
    from app.models.resource import Resource
    from app.models.service import Service
    from app.models.service_extra import ServiceExtra
    from app.models.staff import Staff


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """Return a timezone-aware UTC datetime for safe comparison.

    SQLAdmin submits form values as naive datetimes (no tzinfo), while values
    already stored in the database are UTC-aware.  Treating a naive value as
    UTC is correct here because the DB column is ``DateTime(timezone=True)``
    and PostgreSQL stores everything in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class BookingStatus(str, enum.Enum):
    requested = "requested"
    pending_approval = "pending_approval"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    rejected = "rejected"
    no_show = "no_show"


VALID_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.requested: {BookingStatus.pending_approval, BookingStatus.confirmed},
    BookingStatus.pending_approval: {BookingStatus.confirmed, BookingStatus.rejected},
    BookingStatus.confirmed: {
        BookingStatus.completed,
        BookingStatus.cancelled,
        BookingStatus.no_show,
    },
    BookingStatus.completed: set(),
    BookingStatus.cancelled: set(),
    BookingStatus.rejected: set(),
    BookingStatus.no_show: set(),
}


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        sa.CheckConstraint("ends_at > starts_at", name="ck_booking_valid_time"),
    )

    def __str__(self) -> str:
        return f"Booking #{self.id} ({self.status})"

    @validates("ends_at")
    def validate_ends_at(self, key: str, ends_at: datetime) -> datetime:
        if self.starts_at is not None and ends_at is not None:
            if _as_utc(ends_at) <= _as_utc(self.starts_at):
                raise ValueError("ends_at must be after starts_at")
        return ends_at

    @validates("starts_at")
    def validate_starts_at(self, key: str, starts_at: datetime) -> datetime:
        if self.ends_at is not None and starts_at is not None:
            if _as_utc(starts_at) >= _as_utc(self.ends_at):
                raise ValueError("starts_at must be before ends_at")
        return starts_at

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        sa.ForeignKey("services.id"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        sa.ForeignKey("customers.id"), nullable=False
    )
    location_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("locations.id"), nullable=True
    )
    starts_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        sa.Enum(BookingStatus, name="booking_status"),
        nullable=False,
        default=BookingStatus.requested,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    amount_due: Mapped[Decimal | None] = mapped_column(sa.Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="bookings")
    service: Mapped[Service] = relationship(back_populates="bookings")
    customer: Mapped[Customer] = relationship(back_populates="bookings")
    location: Mapped[Location | None] = relationship(back_populates="bookings")
    booking_staff: Mapped[list[BookingStaff]] = relationship(back_populates="booking")
    booking_resources: Mapped[list[BookingResource]] = relationship(back_populates="booking")
    extras: Mapped[list[BookingExtra]] = relationship(back_populates="booking")


class BookingStaff(Base):
    __tablename__ = "booking_staff"

    def __str__(self) -> str:
        return f"BookingStaff #{self.id}"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    staff_id: Mapped[int] = mapped_column(
        sa.ForeignKey("staff.id"), nullable=False
    )

    booking: Mapped[Booking] = relationship(back_populates="booking_staff")
    staff_member: Mapped[Staff] = relationship(back_populates="booking_staff")


class BookingResource(Base):
    __tablename__ = "booking_resources"

    def __str__(self) -> str:
        return f"BookingResource #{self.id}"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    resource_id: Mapped[int] = mapped_column(
        sa.ForeignKey("resources.id"), nullable=False
    )

    booking: Mapped[Booking] = relationship(back_populates="booking_resources")
    resource: Mapped[Resource] = relationship(back_populates="booking_resources")


class BookingExtra(Base):
    __tablename__ = "booking_extras"

    def __str__(self) -> str:
        return f"BookingExtra #{self.id}"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    service_extra_id: Mapped[int] = mapped_column(
        sa.ForeignKey("service_extras.id"), nullable=False
    )

    booking: Mapped[Booking] = relationship(back_populates="extras")
    extra: Mapped[ServiceExtra] = relationship(back_populates="booking_extras")
