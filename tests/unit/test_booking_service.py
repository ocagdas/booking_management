"""Tests for the booking and approval engine (Phase 4)."""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.booking import BookingStatus
from app.models.business import Business
from app.models.customer import Customer
from app.models.service import ApprovalMode, Service
from app.schemas.booking import BookingCreateRequest
from app.services import booking_service

_UTC = timezone.utc

_T0 = datetime(2025, 6, 1, 9, 0, 0, tzinfo=_UTC)
_T1 = datetime(2025, 6, 1, 10, 0, 0, tzinfo=_UTC)


def _unique_slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _req(biz_id: int, svc_id: int, cust_id: int, **kwargs) -> BookingCreateRequest:
    return BookingCreateRequest(
        business_id=biz_id,
        service_id=svc_id,
        customer_id=cust_id,
        starts_at=_T0,
        ends_at=_T1,
        **kwargs,
    )


@pytest.fixture
def auto_setup(db_session: Session):
    biz = Business(name="AutoGarage", slug=_unique_slug("autogarage"))
    db_session.add(biz)
    db_session.flush()
    svc = Service(
        business_id=biz.id,
        name="Quick Wash",
        duration_minutes=60,
        unit_price=10,
        approval_mode=ApprovalMode.auto,
    )
    cust = Customer(business_id=biz.id, name="Alice")
    db_session.add_all([svc, cust])
    db_session.flush()
    return biz, svc, cust


@pytest.fixture
def manual_setup(db_session: Session):
    biz = Business(name="ManualGarage", slug=_unique_slug("manualgarage"))
    db_session.add(biz)
    db_session.flush()
    svc = Service(
        business_id=biz.id,
        name="Full Service",
        duration_minutes=120,
        unit_price=20,
        approval_mode=ApprovalMode.manual,
    )
    cust = Customer(business_id=biz.id, name="Bob")
    db_session.add_all([svc, cust])
    db_session.flush()
    return biz, svc, cust


class TestCreateBooking:
    def test_auto_service_creates_confirmed_booking(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        assert booking.status == BookingStatus.confirmed

    def test_manual_service_creates_pending_booking(self, db_session, manual_setup):
        biz, svc, cust = manual_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        assert booking.status == BookingStatus.pending_approval

    def test_booking_creation_writes_audit_log(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        log = db_session.query(AuditLog).filter_by(entity_id=booking.id).first()
        assert log is not None
        assert log.action == "booking_created"

    def test_missing_service_raises_404(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        with pytest.raises(HTTPException) as exc:
            booking_service.create_booking(db_session, _req(biz.id, 99999, cust.id))
        assert exc.value.status_code == 404

    def test_ends_at_before_starts_at_raises_422(self, db_session, auto_setup):
        """Service-layer defence: rejects inverted times even if Pydantic is bypassed."""
        biz, svc, cust = auto_setup
        req = BookingCreateRequest.model_construct(
            business_id=biz.id,
            service_id=svc.id,
            customer_id=cust.id,
            starts_at=_T1,
            ends_at=_T0,  # ends before it starts
            resource_ids=[],
            staff_ids=[],
        )
        with pytest.raises(HTTPException) as exc:
            booking_service.create_booking(db_session, req)
        assert exc.value.status_code == 422

    def test_ends_at_equal_starts_at_raises_422(self, db_session, auto_setup):
        """Service-layer defence: rejects equal start/end times."""
        biz, svc, cust = auto_setup
        req = BookingCreateRequest.model_construct(
            business_id=biz.id,
            service_id=svc.id,
            customer_id=cust.id,
            starts_at=_T0,
            ends_at=_T0,
            resource_ids=[],
            staff_ids=[],
        )
        with pytest.raises(HTTPException) as exc:
            booking_service.create_booking(db_session, req)
        assert exc.value.status_code == 422


class TestApproveBooking:
    def test_approve_pending_booking(self, db_session, manual_setup):
        biz, svc, cust = manual_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        assert booking.status == BookingStatus.pending_approval
        approved = booking_service.approve_booking(db_session, booking.id, actor="admin")
        assert approved.status == BookingStatus.confirmed

    def test_approve_writes_audit_log(self, db_session, manual_setup):
        biz, svc, cust = manual_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        booking_service.approve_booking(db_session, booking.id, actor="admin")
        logs = db_session.query(AuditLog).filter_by(entity_id=booking.id).all()
        actions = [l.action for l in logs]
        assert "booking_approved" in actions

    def test_invalid_transition_raises_422(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        assert booking.status == BookingStatus.confirmed
        # Cannot approve an already confirmed booking
        with pytest.raises(HTTPException) as exc:
            booking_service.approve_booking(db_session, booking.id)
        assert exc.value.status_code == 422


class TestRejectBooking:
    def test_reject_pending_booking(self, db_session, manual_setup):
        biz, svc, cust = manual_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        rejected = booking_service.reject_booking(
            db_session, booking.id, actor="admin", reason="Fully booked"
        )
        assert rejected.status == BookingStatus.rejected

    def test_cannot_reject_confirmed_booking(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        with pytest.raises(HTTPException) as exc:
            booking_service.reject_booking(db_session, booking.id)
        assert exc.value.status_code == 422


class TestCompleteBooking:
    def test_complete_confirmed_booking(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        completed = booking_service.complete_booking(db_session, booking.id)
        assert completed.status == BookingStatus.completed

    def test_complete_writes_audit_log(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        booking_service.complete_booking(db_session, booking.id)
        logs = db_session.query(AuditLog).filter_by(entity_id=booking.id).all()
        assert any(l.action == "booking_completed" for l in logs)


class TestGetBooking:
    def test_get_existing_booking(self, db_session, auto_setup):
        biz, svc, cust = auto_setup
        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        fetched = booking_service.get_booking(db_session, booking.id)
        assert fetched.id == booking.id

    def test_get_missing_booking_raises_404(self, db_session):
        with pytest.raises(HTTPException) as exc:
            booking_service.get_booking(db_session, 99999)
        assert exc.value.status_code == 404


class TestAmountDue:
    def test_flat_fee_ignores_duration(self):
        from decimal import Decimal
        from app.models.service import PriceUnit, calculate_amount_due

        result = calculate_amount_due(Decimal("25.00"), PriceUnit.flat, 90)
        assert result == Decimal("25.00")

    def test_per_hour_rate(self):
        from decimal import Decimal
        from app.models.service import PriceUnit, calculate_amount_due

        # £10/hour × 90 min = £15.00
        result = calculate_amount_due(Decimal("10.00"), PriceUnit.per_hour, 90)
        assert result == Decimal("15.00")

    def test_per_5_min_rate(self):
        from decimal import Decimal
        from app.models.service import PriceUnit, calculate_amount_due

        # £2 per 5 min × (30 min / 5) = £12.00
        result = calculate_amount_due(Decimal("2.00"), PriceUnit.per_5_min, 30)
        assert result == Decimal("12.00")

    def test_amount_due_stored_on_booking(self, db_session, auto_setup):
        from decimal import Decimal
        from app.models.service import PriceUnit

        biz, svc, cust = auto_setup
        svc.unit_price = Decimal("10.00")
        svc.price_unit = PriceUnit.per_hour
        db_session.flush()

        booking = booking_service.create_booking(db_session, _req(biz.id, svc.id, cust.id))
        # 60 min at £10/hour = £10.00
        assert booking.amount_due == Decimal("10.00")
