"""Public booking page routes — Jinja2 + HTMX server-rendered flow."""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.booking import BookingStatus
from app.models.business import Business
from app.models.customer import Customer
from app.models.service import Service
from app.schemas.booking import BookingCreateRequest
from app.services import booking_service

router = APIRouter(prefix="/book", tags=["public"])
templates = Jinja2Templates(directory="app/templates")

_UTC = timezone.utc
_SLOT_HOURS = list(range(8, 18))  # 08:00–17:00 on the hour


def _get_business(slug: str, db: Session) -> Business:
    business = db.scalar(select(Business).where(Business.slug == slug))
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


# ------------------------------------------------------------------
# GET /book/{slug}  — service list
# ------------------------------------------------------------------
@router.get("/{slug}", response_class=HTMLResponse)
def services_page(slug: str, request: Request, db: Session = Depends(get_db_session)):
    business = _get_business(slug, db)
    services = db.scalars(
        select(Service)
        .where(Service.business_id == business.id, Service.is_active.is_(True))
        .order_by(Service.name)
    ).all()
    return templates.TemplateResponse(
        "public/services.html",
        {"request": request, "business": business, "services": services},
    )


# ------------------------------------------------------------------
# GET /book/{slug}/{service_id}/slot  — choose date/time
# ------------------------------------------------------------------
@router.get("/{slug}/{service_id}/slot", response_class=HTMLResponse)
def slot_page(
    slug: str, service_id: int, request: Request, db: Session = Depends(get_db_session)
):
    business = _get_business(slug, db)
    service = db.get(Service, service_id)
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")
    today = date.today().isoformat()
    return templates.TemplateResponse(
        "public/slot.html",
        {"request": request, "business": business, "service": service, "today": today},
    )


# ------------------------------------------------------------------
# GET /book/{slug}/{service_id}/slots  — HTMX fragment: available times
# ------------------------------------------------------------------
@router.get("/{slug}/{service_id}/slots", response_class=HTMLResponse)
def slots_fragment(
    slug: str,
    service_id: int,
    request: Request,
    date: str = "",
    db: Session = Depends(get_db_session),
):
    business = _get_business(slug, db)
    service = db.get(Service, service_id)
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")

    slots: list[str] = []
    if date:
        try:
            chosen_date = datetime.fromisoformat(date).date()
        except ValueError:
            chosen_date = None

        if chosen_date:
            for hour in _SLOT_HOURS:
                starts_at = datetime(
                    chosen_date.year, chosen_date.month, chosen_date.day, hour, 0, 0, tzinfo=_UTC
                )
                ends_at = starts_at + timedelta(minutes=service.duration_minutes)
                slots.append(starts_at.isoformat())

    return templates.TemplateResponse(
        "public/slots_fragment.html",
        {
            "request": request,
            "slots": slots,
            "business_slug": slug,
            "service_id": service_id,
        },
    )


# ------------------------------------------------------------------
# GET /book/{slug}/{service_id}/details  — customer details form
# ------------------------------------------------------------------
@router.get("/{slug}/{service_id}/details", response_class=HTMLResponse)
def details_page(
    slug: str,
    service_id: int,
    starts_at: str,
    request: Request,
    db: Session = Depends(get_db_session),
    error: str = "",
):
    business = _get_business(slug, db)
    service = db.get(Service, service_id)
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        starts_at_dt = datetime.fromisoformat(starts_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid starts_at format")
    return templates.TemplateResponse(
        "public/details.html",
        {
            "request": request,
            "business": business,
            "service": service,
            "starts_at": starts_at_dt,
            "starts_at_iso": starts_at,
            "error": error,
        },
    )


# ------------------------------------------------------------------
# POST /book/{slug}/{service_id}/confirm  — submit booking
# ------------------------------------------------------------------
@router.post("/{slug}/{service_id}/confirm", response_class=HTMLResponse)
def confirm_booking(
    slug: str,
    service_id: int,
    request: Request,
    starts_at: str = Form(...),
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db_session),
):
    business = _get_business(slug, db)
    service = db.get(Service, service_id)
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")

    try:
        starts_at_dt = datetime.fromisoformat(starts_at)
        if starts_at_dt.tzinfo is None:
            starts_at_dt = starts_at_dt.replace(tzinfo=_UTC)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid starts_at")

    ends_at_dt = starts_at_dt + timedelta(minutes=service.duration_minutes)

    # Find or create the customer record for this business.
    customer = db.scalar(
        select(Customer).where(
            Customer.business_id == business.id,
            Customer.name == name,
            Customer.email == (email or None),
        )
    )
    if customer is None:
        customer = Customer(
            business_id=business.id,
            name=name,
            email=email or None,
            phone=phone or None,
        )
        db.add(customer)
        db.flush()

    req = BookingCreateRequest(
        business_id=business.id,
        service_id=service.id,
        customer_id=customer.id,
        starts_at=starts_at_dt,
        ends_at=ends_at_dt,
        notes=notes or None,
    )
    booking = booking_service.create_booking(db, req)

    return templates.TemplateResponse(
        "public/result.html",
        {
            "request": request,
            "business": business,
            "business_slug": slug,
            "service": service,
            "booking": booking,
        },
    )
