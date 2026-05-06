"""Tests for the availability engine (Phase 3)."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingResource, BookingStaff, BookingStatus
from app.models.business import Business
from app.models.customer import Customer
from app.models.resource import Resource
from app.models.service import ApprovalMode, Service
from app.models.staff import Staff
from app.services.availability_service import (
    check_resource_available,
    check_staff_available,
    is_business_slot_available,
)

_UTC = timezone.utc


def _make_dt(hour: int) -> datetime:
    return datetime(2025, 6, 1, hour, 0, 0, tzinfo=_UTC)


@pytest.fixture
def setup(db_session: Session):
    """Seed one business, service, resource, staff member."""
    biz = Business(name="Test Garage", slug=f"test-garage-{uuid.uuid4().hex[:8]}")
    db_session.add(biz)
    db_session.flush()

    svc = Service(
        business_id=biz.id,
        name="MOT",
        duration_minutes=60,
        unit_price=0,
        approval_mode=ApprovalMode.auto,
    )
    resource = Resource(business_id=biz.id, name="Bay 1")
    staff = Staff(business_id=biz.id, name="Alice")
    db_session.add_all([svc, resource, staff])
    db_session.flush()

    customer = Customer(business_id=biz.id, name="Bob")
    db_session.add(customer)
    db_session.flush()

    return {"biz": biz, "svc": svc, "resource": resource, "staff": staff, "customer": customer}


def _make_booking(
    db: Session,
    setup: dict,
    starts_at: datetime,
    ends_at: datetime,
    status: BookingStatus = BookingStatus.confirmed,
    with_resource: bool = True,
    with_staff: bool = True,
) -> Booking:
    s = setup
    booking = Booking(
        business_id=s["biz"].id,
        service_id=s["svc"].id,
        customer_id=s["customer"].id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=status,
    )
    db.add(booking)
    db.flush()
    if with_resource:
        db.add(BookingResource(booking_id=booking.id, resource_id=s["resource"].id))
    if with_staff:
        db.add(BookingStaff(booking_id=booking.id, staff_id=s["staff"].id))
    db.flush()
    return booking


class TestResourceAvailability:
    def test_no_bookings_available(self, db_session, setup):
        assert check_resource_available(
            db_session, setup["resource"].id, _make_dt(9), _make_dt(10)
        )

    def test_same_resource_overlapping_rejected(self, db_session, setup):
        _make_booking(db_session, setup, _make_dt(9), _make_dt(10))
        # Request 09:30–10:30 overlaps
        assert not check_resource_available(
            db_session, setup["resource"].id, _make_dt(9), _make_dt(10)
        )

    def test_same_resource_non_overlapping_accepted(self, db_session, setup):
        _make_booking(db_session, setup, _make_dt(9), _make_dt(10))
        # Request 10:00–11:00 is adjacent, not overlapping
        assert check_resource_available(
            db_session, setup["resource"].id, _make_dt(10), _make_dt(11)
        )

    def test_different_resource_overlapping_accepted(self, db_session, setup):
        _make_booking(db_session, setup, _make_dt(9), _make_dt(10))
        other_resource = Resource(business_id=setup["biz"].id, name="Bay 2")
        db_session.add(other_resource)
        db_session.flush()
        assert check_resource_available(
            db_session, other_resource.id, _make_dt(9), _make_dt(10)
        )

    def test_cancelled_booking_does_not_block(self, db_session, setup):
        _make_booking(
            db_session, setup, _make_dt(9), _make_dt(10), status=BookingStatus.cancelled
        )
        assert check_resource_available(
            db_session, setup["resource"].id, _make_dt(9), _make_dt(10)
        )


class TestStaffAvailability:
    def test_no_bookings_available(self, db_session, setup):
        assert check_staff_available(
            db_session, setup["staff"].id, _make_dt(9), _make_dt(10)
        )

    def test_same_staff_overlapping_rejected(self, db_session, setup):
        _make_booking(db_session, setup, _make_dt(9), _make_dt(10))
        assert not check_staff_available(
            db_session, setup["staff"].id, _make_dt(9), _make_dt(10)
        )

    def test_same_staff_non_overlapping_accepted(self, db_session, setup):
        _make_booking(db_session, setup, _make_dt(9), _make_dt(10))
        assert check_staff_available(
            db_session, setup["staff"].id, _make_dt(10), _make_dt(11)
        )

    def test_rejected_booking_does_not_block(self, db_session, setup):
        _make_booking(
            db_session, setup, _make_dt(9), _make_dt(10), status=BookingStatus.rejected
        )
        assert check_staff_available(
            db_session, setup["staff"].id, _make_dt(9), _make_dt(10)
        )


class TestResourceCapacity:
    """Resource.count allows N concurrent bookings before blocking."""

    def test_count_2_allows_two_concurrent(self, db_session, setup):
        resource = setup["resource"]
        resource.count = 2
        db_session.flush()

        _make_booking(db_session, setup, _make_dt(9), _make_dt(10), with_staff=False)
        # First booking: 1 concurrent < 2 → still available
        assert check_resource_available(
            db_session, resource.id, _make_dt(9), _make_dt(10)
        )

    def test_count_2_blocks_third_concurrent(self, db_session, setup):
        resource = setup["resource"]
        resource.count = 2
        db_session.flush()

        _make_booking(db_session, setup, _make_dt(9), _make_dt(10), with_staff=False)
        # Add a second booking for the same resource same slot
        b2 = Booking(
            business_id=setup["biz"].id,
            service_id=setup["svc"].id,
            customer_id=setup["customer"].id,
            starts_at=_make_dt(9),
            ends_at=_make_dt(10),
            status=BookingStatus.confirmed,
        )
        db_session.add(b2)
        db_session.flush()
        db_session.add(BookingResource(booking_id=b2.id, resource_id=resource.id))
        db_session.flush()

        # Two concurrent bookings == capacity; third must be blocked
        assert not check_resource_available(
            db_session, resource.id, _make_dt(9), _make_dt(10)
        )


class TestIsBusinessSlotAvailable:
    def test_no_resources_no_bookings_available(self, db_session, setup):
        # Business with no resources configured, no bookings yet
        biz = Business(name="Solo Biz", slug=f"solo-{uuid.uuid4().hex[:8]}")
        db_session.add(biz)
        db_session.flush()
        assert is_business_slot_available(db_session, biz.id, _make_dt(9), _make_dt(10))

    def test_no_resources_one_booking_blocks(self, db_session, setup):
        # When no resources, second booking for same slot is blocked
        biz = Business(name="Solo Biz2", slug=f"solo2-{uuid.uuid4().hex[:8]}")
        db_session.add(biz)
        db_session.flush()
        svc = Service(
            business_id=biz.id,
            name="Cut",
            duration_minutes=30,
            unit_price=0,
            approval_mode="auto",
        )
        cust = Customer(business_id=biz.id, name="Dave")
        db_session.add_all([svc, cust])
        db_session.flush()
        b = Booking(
            business_id=biz.id,
            service_id=svc.id,
            customer_id=cust.id,
            starts_at=_make_dt(9),
            ends_at=_make_dt(10),
            status=BookingStatus.confirmed,
        )
        db_session.add(b)
        db_session.flush()
        assert not is_business_slot_available(db_session, biz.id, _make_dt(9), _make_dt(10))

    def test_with_resources_available_capacity(self, db_session, setup):
        # Business has a resource with count=2; one booking → slot still available
        r = Resource(business_id=setup["biz"].id, name="Table A", count=2)
        db_session.add(r)
        db_session.flush()

        b = Booking(
            business_id=setup["biz"].id,
            service_id=setup["svc"].id,
            customer_id=setup["customer"].id,
            starts_at=_make_dt(11),
            ends_at=_make_dt(12),
            status=BookingStatus.confirmed,
        )
        db_session.add(b)
        db_session.flush()
        db_session.add(BookingResource(booking_id=b.id, resource_id=r.id))
        db_session.flush()

        # resource r has capacity=2, used=1 → slot still available
        assert is_business_slot_available(db_session, setup["biz"].id, _make_dt(11), _make_dt(12))
