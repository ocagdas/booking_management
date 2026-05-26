from datetime import date, datetime, time, timezone

from app.models.booking import Booking
from app.models.enums import BookingStatus, GapUnit
from app.models.location import LocationBreak
from app.services.availability_service import available_start_times
from tests.unit.helpers import seed_hairdresser


MONDAY = date(2026, 6, 1)
UTC = timezone.utc


def _slot(hour: int, minute: int = 0):
    return datetime(2026, 6, 1, hour, minute, tzinfo=UTC)


def test_available_start_times_do_not_exceed_close_minus_duration_and_gap(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.fixed_duration_value = 60
    service.gap_after_value = 30
    service.gap_after_unit = GapUnit.minutes.value
    db_session.commit()

    slots = available_start_times(
        db_session,
        business_id=business.id,
        location_id=location.id,
        staff_id=staff.id,
        service=service,
        day=MONDAY,
        interval_minutes=60,
    )

    assert _slot(15, 30) not in slots
    assert _slot(16, 0) not in slots
    assert slots[-1] == _slot(15, 0)


def test_available_start_times_exclude_breaks(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    db_session.add(
        LocationBreak(
            location_id=location.id,
            day_of_week=0,
            starts_at=time(12, 0),
            ends_at=time(13, 0),
        )
    )
    db_session.commit()

    slots = available_start_times(
        db_session,
        business_id=business.id,
        location_id=location.id,
        staff_id=staff.id,
        service=service,
        day=MONDAY,
        interval_minutes=30,
    )

    assert _slot(12, 0) not in slots
    assert _slot(12, 30) not in slots
    assert _slot(11, 30) in slots
    assert _slot(13, 0) in slots


def test_confirmed_booking_blocks_availability(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    db_session.add(
        Booking(
            business_id=business.id,
            location_id=location.id,
            service_id=service.id,
            staff_id=staff.id,
            customer_id=customer.id,
            selected_duration_value=30,
            selected_duration_unit="minutes",
            starts_at=_slot(10),
            ends_at=_slot(10, 30),
            gap_after_value=0,
            gap_after_unit="minutes",
            blocked_until=_slot(10, 30),
            status=BookingStatus.confirmed.value,
        )
    )
    db_session.commit()

    slots = available_start_times(
        db_session,
        business_id=business.id,
        location_id=location.id,
        staff_id=staff.id,
        service=service,
        day=MONDAY,
        interval_minutes=30,
    )

    assert _slot(10) not in slots


def test_pending_approval_booking_blocks_availability(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    db_session.add(
        Booking(
            business_id=business.id,
            location_id=location.id,
            service_id=service.id,
            staff_id=staff.id,
            customer_id=customer.id,
            selected_duration_value=30,
            selected_duration_unit="minutes",
            starts_at=_slot(10),
            ends_at=_slot(10, 30),
            gap_after_value=0,
            gap_after_unit="minutes",
            blocked_until=_slot(10, 30),
            status=BookingStatus.pending_approval.value,
        )
    )
    db_session.commit()

    slots = available_start_times(
        db_session,
        business_id=business.id,
        location_id=location.id,
        staff_id=staff.id,
        service=service,
        day=MONDAY,
        interval_minutes=30,
    )

    assert _slot(10) not in slots


def test_rejected_and_cancelled_bookings_do_not_block_availability(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    for status in [BookingStatus.rejected.value, BookingStatus.cancelled.value]:
        db_session.add(
            Booking(
                business_id=business.id,
                location_id=location.id,
                service_id=service.id,
                staff_id=staff.id,
                customer_id=customer.id,
                selected_duration_value=30,
                selected_duration_unit="minutes",
                starts_at=_slot(10),
                ends_at=_slot(10, 30),
                gap_after_value=0,
                gap_after_unit="minutes",
                blocked_until=_slot(10, 30),
                status=status,
            )
        )
    db_session.commit()

    slots = available_start_times(
        db_session,
        business_id=business.id,
        location_id=location.id,
        staff_id=staff.id,
        service=service,
        day=MONDAY,
        interval_minutes=30,
    )

    assert _slot(10) in slots
