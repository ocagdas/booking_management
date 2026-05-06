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
        price_pence=1000,
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
        price_pence=8000,
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
