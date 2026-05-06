"""Booking service — create, approve, reject bookings and enforce domain rules."""
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import (
    Booking,
    BookingResource,
    BookingStaff,
    BookingStatus,
    VALID_TRANSITIONS,
)
from app.models.service import ApprovalMode, Service
from app.schemas.booking import BookingCreateRequest
from app.services import audit_service, availability_service


class ConflictError(Exception):
    """Raised when a resource or staff member is already booked."""


def create_booking(session: Session, req: BookingCreateRequest) -> Booking:
    """Create a booking, run availability checks, and apply approval rules."""
    if req.ends_at <= req.starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ends_at must be after starts_at",
        )

    service = session.get(Service, req.service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    # Availability checks for every requested resource and staff member.
    for rid in req.resource_ids:
        if not availability_service.check_resource_available(
            session, rid, req.starts_at, req.ends_at
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource {rid} is not available for the requested time slot",
            )

    for sid in req.staff_ids:
        if not availability_service.check_staff_available(
            session, sid, req.starts_at, req.ends_at
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Staff member {sid} is not available for the requested time slot",
            )

    # Determine initial status from the service's approval mode.
    if service.approval_mode == ApprovalMode.auto:
        initial_status = BookingStatus.confirmed
    elif service.approval_mode == ApprovalMode.manual:
        initial_status = BookingStatus.pending_approval
    else:
        # hybrid — default to pending_approval; callers can override via config
        initial_status = BookingStatus.pending_approval

    booking = Booking(
        business_id=req.business_id,
        service_id=req.service_id,
        customer_id=req.customer_id,
        location_id=req.location_id,
        starts_at=req.starts_at,
        ends_at=req.ends_at,
        status=initial_status,
        notes=req.notes,
    )
    session.add(booking)
    session.flush()  # get booking.id

    for rid in req.resource_ids:
        session.add(BookingResource(booking_id=booking.id, resource_id=rid))

    for sid in req.staff_ids:
        session.add(BookingStaff(booking_id=booking.id, staff_id=sid))

    audit_service.log_event(
        session,
        entity_type="booking",
        entity_id=booking.id,
        action="booking_created",
        business_id=req.business_id,
        payload={"status": initial_status.value},
    )

    session.commit()
    session.refresh(booking)
    return booking


def _transition(
    session: Session,
    booking_id: int,
    target_status: BookingStatus,
    actor: str | None,
    action_name: str,
    payload: dict | None = None,
) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    allowed = VALID_TRANSITIONS.get(booking.status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Cannot move booking from '{booking.status.value}' "
                f"to '{target_status.value}'"
            ),
        )

    previous = booking.status
    booking.status = target_status

    audit_service.log_event(
        session,
        entity_type="booking",
        entity_id=booking.id,
        action=action_name,
        business_id=booking.business_id,
        actor=actor,
        payload={**(payload or {}), "from": previous.value, "to": target_status.value},
    )

    session.commit()
    session.refresh(booking)
    return booking


def approve_booking(
    session: Session, booking_id: int, actor: str | None = None
) -> Booking:
    """Move a booking from pending_approval → confirmed."""
    return _transition(
        session,
        booking_id,
        BookingStatus.confirmed,
        actor=actor,
        action_name="booking_approved",
    )


def reject_booking(
    session: Session,
    booking_id: int,
    actor: str | None = None,
    reason: str | None = None,
) -> Booking:
    """Move a booking to rejected."""
    return _transition(
        session,
        booking_id,
        BookingStatus.rejected,
        actor=actor,
        action_name="booking_rejected",
        payload={"reason": reason} if reason else None,
    )


def cancel_booking(
    session: Session,
    booking_id: int,
    actor: str | None = None,
    reason: str | None = None,
) -> Booking:
    """Move a booking to cancelled."""
    return _transition(
        session,
        booking_id,
        BookingStatus.cancelled,
        actor=actor,
        action_name="booking_cancelled",
        payload={"reason": reason} if reason else None,
    )


def complete_booking(
    session: Session, booking_id: int, actor: str | None = None
) -> Booking:
    """Move a booking to completed."""
    return _transition(
        session,
        booking_id,
        BookingStatus.completed,
        actor=actor,
        action_name="booking_completed",
    )


def get_booking(session: Session, booking_id: int) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking
