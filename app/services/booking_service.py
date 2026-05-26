from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import ApprovalMode, BookingStatus
from app.models.service import Service
from app.schemas.booking import BookingCreate
from app.services import audit_service, availability_service
from app.services.duration_service import add_minutes, resolve_gap, resolve_service_duration


def create_booking(session: Session, req: BookingCreate) -> Booking:
    service = session.get(Service, req.service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    duration_minutes, selected_value, selected_unit = resolve_service_duration(
        service,
        selected_duration_value=req.selected_duration_value,
        selected_duration_unit=req.selected_duration_unit,
    )
    gap_minutes, gap_value, gap_unit = resolve_gap(
        service,
        gap_after_value=req.gap_after_value,
        gap_after_unit=req.gap_after_unit,
    )
    ends_at = req.starts_at + add_minutes(duration_minutes)
    blocked_until = ends_at + add_minutes(gap_minutes)

    if not availability_service.is_slot_available(
        session,
        business_id=req.business_id,
        location_id=req.location_id,
        staff_id=req.staff_id,
        starts_at=req.starts_at,
        ends_at=ends_at,
        blocked_until=blocked_until,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected start time is not available",
        )

    booking = Booking(
        business_id=req.business_id,
        location_id=req.location_id,
        service_id=req.service_id,
        staff_id=req.staff_id,
        customer_id=req.customer_id,
        selected_duration_value=selected_value,
        selected_duration_unit=selected_unit,
        starts_at=req.starts_at,
        ends_at=ends_at,
        gap_after_value=gap_value,
        gap_after_unit=gap_unit,
        blocked_until=blocked_until,
        status=(
            BookingStatus.confirmed.value
            if service.approval_mode == ApprovalMode.auto.value
            else BookingStatus.pending_approval.value
        ),
        notes=req.notes,
    )
    session.add(booking)
    session.flush()
    audit_service.log_event(
        session,
        business_id=booking.business_id,
        entity_type="booking",
        entity_id=booking.id,
        action="booking_created",
        payload={"status": booking.status},
    )
    session.commit()
    session.refresh(booking)
    _restore_utc(booking)
    return booking


def approve_booking(session: Session, booking_id: int) -> Booking:
    booking = _get_booking(session, booking_id)
    if booking.status != BookingStatus.pending_approval.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only pending approval bookings can be approved",
        )
    booking.status = BookingStatus.confirmed.value
    audit_service.log_event(
        session,
        business_id=booking.business_id,
        entity_type="booking",
        entity_id=booking.id,
        action="booking_approved",
    )
    session.commit()
    session.refresh(booking)
    _restore_utc(booking)
    return booking


def reject_booking(session: Session, booking_id: int) -> Booking:
    booking = _get_booking(session, booking_id)
    if booking.status != BookingStatus.pending_approval.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only pending approval bookings can be rejected",
        )
    booking.status = BookingStatus.rejected.value
    audit_service.log_event(
        session,
        business_id=booking.business_id,
        entity_type="booking",
        entity_id=booking.id,
        action="booking_rejected",
    )
    session.commit()
    session.refresh(booking)
    _restore_utc(booking)
    return booking


def cancel_booking(session: Session, booking_id: int) -> Booking:
    booking = _get_booking(session, booking_id)
    booking.status = BookingStatus.cancelled.value
    audit_service.log_event(
        session,
        business_id=booking.business_id,
        entity_type="booking",
        entity_id=booking.id,
        action="booking_cancelled",
    )
    session.commit()
    session.refresh(booking)
    _restore_utc(booking)
    return booking


def _get_booking(session: Session, booking_id: int) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


def _restore_utc(booking: Booking) -> None:
    """SQLite drops tzinfo; keep service return values timezone-aware."""
    for field in ("starts_at", "ends_at", "blocked_until"):
        value = getattr(booking, field)
        if value is not None and value.tzinfo is None:
            setattr(booking, field, value.replace(tzinfo=timezone.utc))
