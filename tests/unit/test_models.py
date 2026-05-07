"""Unit tests for Phase 1 core models.

Each test exercises a Phase 1 acceptance criterion without a running
PostgreSQL instance.  An in-memory SQLite database is used instead.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.audit import AuditLog
from app.models.booking import Booking, BookingResource, BookingStaff, BookingStatus
from app.models.business import Business, Location
from app.models.customer import Customer
from app.models.resource import Resource
from app.models.service import ApprovalMode, Service
from app.models.staff import Role, Staff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_business(session, name: str = "Test Business", slug: str = "test-biz") -> Business:
    business = Business(name=name, slug=slug)
    session.add(business)
    session.flush()
    return business


def _make_service(session, business_id: int, name: str = "Test Service") -> Service:
    service = Service(
        business_id=business_id,
        name=name,
        duration_minutes=60,
        unit_price=0,
        approval_mode=ApprovalMode.auto,
    )
    session.add(service)
    session.flush()
    return service


def _make_customer(session, business_id: int, name: str = "Alice") -> Customer:
    customer = Customer(
        business_id=business_id,
        name=name,
        email="alice@example.com",
    )
    session.add(customer)
    session.flush()
    return customer


# ---------------------------------------------------------------------------
# Acceptance criteria tests
# ---------------------------------------------------------------------------


def test_create_business(db_session) -> None:
    """Create business succeeds and assigns a primary key."""
    business = _make_business(db_session)

    assert business.id is not None
    assert business.name == "Test Business"
    assert business.slug == "test-biz"


def test_create_service_linked_to_business(db_session) -> None:
    """Create service succeeds and is linked to a business."""
    business = _make_business(db_session, name="Garage", slug="garage")
    service = _make_service(db_session, business.id, name="MOT")

    assert service.id is not None
    assert service.business_id == business.id
    assert service.approval_mode == ApprovalMode.auto
    assert service.is_active is True


def test_create_resource_linked_to_business(db_session) -> None:
    """Create resource succeeds and is linked to a business."""
    business = _make_business(db_session, name="Clinic", slug="clinic")
    resource = Resource(business_id=business.id, name="Treatment Room", resource_type="room")
    db_session.add(resource)
    db_session.flush()

    assert resource.id is not None
    assert resource.business_id == business.id


def test_create_customer_linked_to_business(db_session) -> None:
    """Create customer succeeds and is linked to a business."""
    business = _make_business(db_session, name="Barber", slug="barber")
    customer = _make_customer(db_session, business.id, name="Bob")

    assert customer.id is not None
    assert customer.business_id == business.id


def test_create_booking(db_session) -> None:
    """Create booking succeeds with valid time range and default status."""
    business = _make_business(db_session, name="Tutor", slug="tutor")
    service = _make_service(db_session, business.id)
    customer = _make_customer(db_session, business.id)

    starts = _now()
    ends = starts + timedelta(hours=1)
    booking = Booking(
        business_id=business.id,
        service_id=service.id,
        customer_id=customer.id,
        starts_at=starts,
        ends_at=ends,
        status=BookingStatus.requested,
    )
    db_session.add(booking)
    db_session.flush()

    assert booking.id is not None
    assert booking.status == BookingStatus.requested


def test_create_booking_with_staff_and_resource(db_session) -> None:
    """Booking can be linked to staff and a resource via junction tables."""
    business = _make_business(db_session, name="Equipment Co", slug="equip")
    service = _make_service(db_session, business.id)
    customer = _make_customer(db_session, business.id)

    staff = Staff(business_id=business.id, name="Charlie")
    resource = Resource(business_id=business.id, name="Bay 1", resource_type="bay")
    db_session.add_all([staff, resource])
    db_session.flush()

    starts = _now()
    booking = Booking(
        business_id=business.id,
        service_id=service.id,
        customer_id=customer.id,
        starts_at=starts,
        ends_at=starts + timedelta(hours=1),
        status=BookingStatus.confirmed,
    )
    db_session.add(booking)
    db_session.flush()

    bs = BookingStaff(booking_id=booking.id, staff_id=staff.id)
    br = BookingResource(booking_id=booking.id, resource_id=resource.id)
    db_session.add_all([bs, br])
    db_session.flush()

    assert bs.id is not None
    assert br.id is not None


def test_invalid_booking_time_fails(db_session) -> None:
    """A booking where ends_at <= starts_at is rejected — either by the ORM
    validator (ValueError) or the DB check constraint (IntegrityError)."""
    business = _make_business(db_session, name="Mobile", slug="mobile")
    service = _make_service(db_session, business.id)
    customer = _make_customer(db_session, business.id)

    starts = _now()
    ends = starts - timedelta(hours=1)  # ends before starts → invalid

    with pytest.raises((ValueError, IntegrityError)):
        booking = Booking(
            business_id=business.id,
            service_id=service.id,
            customer_id=customer.id,
            starts_at=starts,
            ends_at=ends,
            status=BookingStatus.requested,
        )
        db_session.add(booking)
        db_session.flush()

    db_session.rollback()


def test_booking_status_choices_enforced(db_session) -> None:
    """An invalid status string is rejected at the Python enum level."""
    with pytest.raises((ValueError, KeyError)):
        BookingStatus("not_a_real_status")


def test_staff_role_linked_to_staff(db_session) -> None:
    """A Role can be created and assigned to a staff member via M2M."""
    business = _make_business(db_session, name="Clinic 2", slug="clinic-2")
    staff = Staff(business_id=business.id, name="Dr Smith")
    db_session.add(staff)
    db_session.flush()

    role = Role(business_id=business.id, name="practitioner")
    db_session.add(role)
    db_session.flush()

    staff.roles.append(role)
    db_session.flush()

    assert role.id is not None
    assert role in staff.roles
    assert staff in role.staff_members


def test_audit_log_created(db_session) -> None:
    """AuditLog can be created with a business reference."""
    business = _make_business(db_session, name="Audit Biz", slug="audit-biz")
    log = AuditLog(
        business_id=business.id,
        entity_type="booking",
        entity_id=1,
        action="created",
        actor="system",
        payload={"note": "test"},
    )
    db_session.add(log)
    db_session.flush()

    assert log.id is not None
    assert log.entity_type == "booking"


def test_location_linked_to_business(db_session) -> None:
    """Location is linked to a business."""
    business = _make_business(db_session, name="Multi-site", slug="multi-site")
    location = Location(business_id=business.id, name="North Branch", address="1 High St")
    db_session.add(location)
    db_session.flush()

    assert location.id is not None
    assert location.business_id == business.id
