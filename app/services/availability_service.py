"""Availability engine — prevents double-booking of resources and staff."""
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingResource, BookingStaff, BookingStatus

# Terminal statuses that no longer occupy a slot.
_INACTIVE_STATUSES = {BookingStatus.cancelled, BookingStatus.rejected, BookingStatus.no_show}


def _active_booking_ids(session: Session, exclude_booking_id: int | None = None):
    """Return a sub-select of booking IDs that are in non-terminal statuses."""
    stmt = select(Booking.id).where(Booking.status.notin_(_INACTIVE_STATUSES))
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return stmt


def check_resource_available(
    session: Session,
    resource_id: int,
    starts_at: datetime,
    ends_at: datetime,
    exclude_booking_id: int | None = None,
) -> bool:
    """Return True if the resource has no overlapping active bookings."""
    active_ids = _active_booking_ids(session, exclude_booking_id)
    conflict = select(
        exists().where(
            BookingResource.resource_id == resource_id,
            BookingResource.booking_id.in_(active_ids),
            Booking.id == BookingResource.booking_id,
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
    )
    return not session.scalar(conflict)


def check_staff_available(
    session: Session,
    staff_id: int,
    starts_at: datetime,
    ends_at: datetime,
    exclude_booking_id: int | None = None,
) -> bool:
    """Return True if the staff member has no overlapping active bookings."""
    active_ids = _active_booking_ids(session, exclude_booking_id)
    conflict = select(
        exists().where(
            BookingStaff.staff_id == staff_id,
            BookingStaff.booking_id.in_(active_ids),
            Booking.id == BookingStaff.booking_id,
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
    )
    return not session.scalar(conflict)
