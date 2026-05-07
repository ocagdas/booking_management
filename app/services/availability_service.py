"""Availability engine — prevents double-booking of resources and staff."""
from datetime import datetime

from sqlalchemy import exists, func, select
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
    """Return True if the resource has remaining capacity for the time window.

    A resource with ``count=N`` can accommodate N concurrent bookings before
    it is considered fully booked.
    """
    from app.models.resource import Resource  # local import avoids circular

    resource = session.get(Resource, resource_id)
    capacity: int = resource.count if resource else 1

    active_ids = _active_booking_ids(session, exclude_booking_id)
    concurrent: int = session.scalar(
        select(func.count()).where(
            BookingResource.resource_id == resource_id,
            BookingResource.booking_id.in_(active_ids),
            Booking.id == BookingResource.booking_id,
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
    ) or 0
    return concurrent < capacity


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


def is_business_slot_available(
    session: Session,
    business_id: int,
    starts_at: datetime,
    ends_at: datetime,
    staff_ids: list[int] | None = None,
) -> bool:
    """Return True if the business can accept at least one more booking.

    When *staff_ids* is provided (non-empty), availability is computed against
    those specific staff members — the slot is available when at least one of
    the selected staff members has no overlapping active booking.

    * If the business has active resources configured (and no staff filter is
      applied), the slot is available when at least one resource still has
      remaining capacity.
    * If no resources are configured, fall back to a one-booking-per-slot
      limit (suitable for simple appointment businesses).
    """
    from app.models.resource import Resource

    if staff_ids:
        return any(
            check_staff_available(session, sid, starts_at, ends_at)
            for sid in staff_ids
        )

    resources = session.scalars(
        select(Resource).where(
            Resource.business_id == business_id,
            Resource.is_active.is_(True),
        )
    ).all()

    if resources:
        return any(
            check_resource_available(session, r.id, starts_at, ends_at)
            for r in resources
        )

    # No resources configured — allow one concurrent booking per time slot.
    count = session.scalar(
        select(func.count(Booking.id)).where(
            Booking.business_id == business_id,
            Booking.status.notin_(_INACTIVE_STATUSES),
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
    ) or 0
    return count == 0

