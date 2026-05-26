from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.audit import AuditLog
from app.models.enums import ApprovalMode, BookingStatus
from app.schemas.booking import BookingCreate
from app.services.booking_service import create_booking, reject_booking
from tests.unit.helpers import seed_hairdresser

UTC = timezone.utc


def _starts_at():
    return datetime(2026, 6, 1, 9, 0, tzinfo=UTC)


def _req(business, location, staff, customer, service, **kwargs):
    return BookingCreate(
        business_id=business.id,
        location_id=location.id,
        service_id=service.id,
        staff_id=staff.id,
        customer_id=customer.id,
        starts_at=_starts_at(),
        **kwargs,
    )


def test_auto_approval_creates_confirmed_booking_and_calculates_end(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)

    booking = create_booking(db_session, _req(business, location, staff, customer, service))

    assert booking.status == BookingStatus.confirmed.value
    assert booking.ends_at == datetime(2026, 6, 1, 9, 30, tzinfo=UTC)
    assert booking.blocked_until == booking.ends_at


def test_manual_approval_creates_pending_booking(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.approval_mode = ApprovalMode.manual.value
    db_session.commit()

    booking = create_booking(db_session, _req(business, location, staff, customer, service))

    assert booking.status == BookingStatus.pending_approval.value


def test_service_gap_blocks_after_end(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.gap_after_value = 15
    db_session.commit()

    booking = create_booking(db_session, _req(business, location, staff, customer, service))

    assert booking.ends_at == datetime(2026, 6, 1, 9, 30, tzinfo=UTC)
    assert booking.blocked_until == datetime(2026, 6, 1, 9, 45, tzinfo=UTC)


def test_booking_gap_override_changes_blocked_until(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.gap_after_value = 15
    db_session.commit()

    booking = create_booking(
        db_session,
        _req(
            business,
            location,
            staff,
            customer,
            service,
            gap_after_value=1,
            gap_after_unit="hours",
        ),
    )

    assert booking.blocked_until == datetime(2026, 6, 1, 10, 30, tzinfo=UTC)


def test_rejecting_pending_booking_releases_slot(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.approval_mode = ApprovalMode.manual.value
    db_session.commit()
    booking = create_booking(db_session, _req(business, location, staff, customer, service))

    rejected = reject_booking(db_session, booking.id)

    assert rejected.status == BookingStatus.rejected.value
    second = create_booking(db_session, _req(business, location, staff, customer, service))
    assert second.id != booking.id


def test_overlapping_confirmed_booking_is_rejected(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    create_booking(db_session, _req(business, location, staff, customer, service))

    with pytest.raises(HTTPException):
        create_booking(db_session, _req(business, location, staff, customer, service))


def test_booking_creation_writes_audit_log(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    booking = create_booking(db_session, _req(business, location, staff, customer, service))

    log = db_session.query(AuditLog).filter_by(entity_id=booking.id).one()

    assert log.action == "booking_created"
