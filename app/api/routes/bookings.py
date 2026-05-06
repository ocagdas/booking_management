"""REST API routes for bookings."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.booking import BookingActionRequest, BookingCreateRequest, BookingResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(
    req: BookingCreateRequest,
    db: Session = Depends(get_db_session),
) -> BookingResponse:
    booking = booking_service.create_booking(db, req)
    return BookingResponse.model_validate(booking)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db_session),
) -> BookingResponse:
    booking = booking_service.get_booking(db, booking_id)
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/approve", response_model=BookingResponse)
def approve_booking(
    booking_id: int,
    req: BookingActionRequest = BookingActionRequest(),
    db: Session = Depends(get_db_session),
) -> BookingResponse:
    booking = booking_service.approve_booking(db, booking_id, actor=req.actor)
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/reject", response_model=BookingResponse)
def reject_booking(
    booking_id: int,
    req: BookingActionRequest = BookingActionRequest(),
    db: Session = Depends(get_db_session),
) -> BookingResponse:
    booking = booking_service.reject_booking(db, booking_id, actor=req.actor, reason=req.reason)
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    req: BookingActionRequest = BookingActionRequest(),
    db: Session = Depends(get_db_session),
) -> BookingResponse:
    booking = booking_service.cancel_booking(db, booking_id, actor=req.actor, reason=req.reason)
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/complete", response_model=BookingResponse)
def complete_booking(
    booking_id: int,
    req: BookingActionRequest = BookingActionRequest(),
    db: Session = Depends(get_db_session),
) -> BookingResponse:
    booking = booking_service.complete_booking(db, booking_id, actor=req.actor)
    return BookingResponse.model_validate(booking)
