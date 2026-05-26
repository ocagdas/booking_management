from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.location import LocationBreak, LocationWorkingHours
from app.models.service import Service
from app.services.duration_service import add_minutes, resolve_gap, resolve_service_duration

BLOCKING_STATUSES = {
    BookingStatus.confirmed.value,
    BookingStatus.pending_approval.value,
}


def _combine(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=timezone.utc)


def windows_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return first_start < second_end and first_end > second_start


def location_hours_for_date(
    session: Session,
    *,
    location_id: int,
    day: date,
) -> LocationWorkingHours | None:
    return session.scalar(
        select(LocationWorkingHours).where(
            LocationWorkingHours.location_id == location_id,
            LocationWorkingHours.day_of_week == day.weekday(),
        )
    )


def breaks_for_date(session: Session, *, location_id: int, day: date) -> list[LocationBreak]:
    return list(
        session.scalars(
            select(LocationBreak)
            .where(
                LocationBreak.location_id == location_id,
                LocationBreak.day_of_week == day.weekday(),
            )
            .order_by(LocationBreak.starts_at)
        )
    )


def is_slot_available(
    session: Session,
    *,
    business_id: int,
    location_id: int,
    staff_id: int,
    starts_at: datetime,
    ends_at: datetime,
    blocked_until: datetime,
) -> bool:
    overlap = session.scalar(
        select(Booking.id)
        .where(
            Booking.business_id == business_id,
            Booking.location_id == location_id,
            Booking.staff_id == staff_id,
            Booking.status.in_(BLOCKING_STATUSES),
            Booking.starts_at < blocked_until,
            Booking.blocked_until > starts_at,
        )
        .limit(1)
    )
    if overlap is not None:
        return False

    day = starts_at.date()
    for location_break in breaks_for_date(session, location_id=location_id, day=day):
        break_start = _combine(day, location_break.starts_at)
        break_end = _combine(day, location_break.ends_at)
        if windows_overlap(starts_at, blocked_until, break_start, break_end):
            return False

    hours = location_hours_for_date(session, location_id=location_id, day=day)
    if hours is None or hours.is_closed or hours.opens_at is None or hours.closes_at is None:
        return False

    opens_at = _combine(day, hours.opens_at)
    closes_at = _combine(day, hours.closes_at)
    return starts_at >= opens_at and blocked_until <= closes_at


def available_start_times(
    session: Session,
    *,
    business_id: int,
    location_id: int,
    staff_id: int,
    service: Service,
    day: date,
    selected_duration_value: int | None = None,
    selected_duration_unit: str | None = None,
    gap_after_value: int | None = None,
    gap_after_unit: str | None = None,
    interval_minutes: int = 15,
) -> list[datetime]:
    hours = location_hours_for_date(session, location_id=location_id, day=day)
    if hours is None or hours.is_closed or hours.opens_at is None or hours.closes_at is None:
        return []

    duration_minutes, _, _ = resolve_service_duration(
        service,
        selected_duration_value=selected_duration_value,
        selected_duration_unit=selected_duration_unit,
    )
    gap_minutes, _, _ = resolve_gap(
        service,
        gap_after_value=gap_after_value,
        gap_after_unit=gap_after_unit,
    )

    opens_at = _combine(day, hours.opens_at)
    closes_at = _combine(day, hours.closes_at)
    starts_at = opens_at
    slots: list[datetime] = []

    while starts_at + add_minutes(duration_minutes + gap_minutes) <= closes_at:
        ends_at = starts_at + add_minutes(duration_minutes)
        blocked_until = ends_at + add_minutes(gap_minutes)
        if is_slot_available(
            session,
            business_id=business_id,
            location_id=location_id,
            staff_id=staff_id,
            starts_at=starts_at,
            ends_at=ends_at,
            blocked_until=blocked_until,
        ):
            slots.append(starts_at)
        starts_at += add_minutes(interval_minutes)

    return slots
