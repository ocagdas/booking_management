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
from app.models.resource import Resource
from app.models.service import Service, calculate_amount_due
from app.models.staff import Staff
from app.schemas.booking import BookingCreateRequest
from app.services import availability_service, booking_service

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
        request,
        "public/services.html",
        {"business": business, "services": services},
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
    # Use service-specific staff/resources if configured; fall back to all business ones.
    staff = service.staff_members if service.staff_members else db.scalars(
        select(Staff)
        .where(Staff.business_id == business.id, Staff.is_active.is_(True))
        .order_by(Staff.name)
    ).all()
    resources = service.resources if service.resources else db.scalars(
        select(Resource)
        .where(Resource.business_id == business.id, Resource.is_active.is_(True))
        .order_by(Resource.name)
    ).all()
    return templates.TemplateResponse(
        request,
        "public/slot.html",
        {
            "business": business,
            "service": service,
            "today": today,
            "staff": staff,
            "resources": resources,
        },
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

    buffer = service.buffer_after_minutes or 0
    slots: list[dict] = []

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
                # Buffer extends the effective window so the next slot can't
                # start within the post-booking idle period.
                effective_end = ends_at + timedelta(minutes=buffer)

                booked = not availability_service.is_business_slot_available(
                    db, business.id, starts_at, effective_end
                )
                slots.append({"iso": starts_at.isoformat(), "booked": booked})

    return templates.TemplateResponse(
        request,
        "public/slots_fragment.html",
        {
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
    # URL-encoding turns '+' into a space; restore it before parsing so that
    # timezone offsets like +00:00 are handled correctly.
    try:
        starts_at_dt = datetime.fromisoformat(starts_at.replace(" ", "+"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid starts_at format")
    ends_at_dt = starts_at_dt + timedelta(minutes=service.duration_minutes)

    duration_minutes = service.duration_minutes
    amount_due = calculate_amount_due(service.unit_price, service.price_unit, duration_minutes)

    # Use service-specific staff/resources if configured; fall back to all business ones.
    staff = service.staff_members if service.staff_members else db.scalars(
        select(Staff)
        .where(Staff.business_id == business.id, Staff.is_active.is_(True))
        .order_by(Staff.name)
    ).all()
    resources = service.resources if service.resources else db.scalars(
        select(Resource)
        .where(Resource.business_id == business.id, Resource.is_active.is_(True))
        .order_by(Resource.name)
    ).all()

    return templates.TemplateResponse(
        request,
        "public/details.html",
        {
            "business": business,
            "service": service,
            "starts_at": starts_at_dt,
            # Use a plain naive UTC string (no + sign) so the hidden form field
            # round-trips cleanly through URL → form → POST without the
            # + ↔ space encoding corruption that afflicts timezone offsets.
            "starts_at_iso": starts_at_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "ends_at": ends_at_dt,
            "ends_at_local": ends_at_dt.strftime("%Y-%m-%dT%H:%M"),
            "staff": staff,
            "resources": resources,
            "extras": service.extras,
            "notes_prompt": service.notes_prompt or "Notes (optional)",
            "amount_due": amount_due,
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
    ends_at: str = Form(...),
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    notes: str = Form(""),
    staff_id: int | None = Form(None),
    resource_ids: list[int] = Form(default=[]),
    extra_ids: list[int] = Form(default=[]),
    db: Session = Depends(get_db_session),
):
    business = _get_business(slug, db)
    service = db.get(Service, service_id)
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")

    try:
        # Defensively handle the + ↔ space encoding issue: a '+' in a query
        # string or form value can arrive as a space after URL decoding.
        starts_at_dt = datetime.fromisoformat(starts_at.replace(" ", "+"))
        if starts_at_dt.tzinfo is None:
            starts_at_dt = starts_at_dt.replace(tzinfo=_UTC)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid starts_at")

    try:
        ends_at_dt = datetime.fromisoformat(ends_at.replace(" ", "+"))
        if ends_at_dt.tzinfo is None:
            ends_at_dt = ends_at_dt.replace(tzinfo=_UTC)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ends_at")

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
        staff_ids=[staff_id] if staff_id else [],
        resource_ids=resource_ids,
        extra_ids=extra_ids,
    )
    booking = booking_service.create_booking(db, req)

    return templates.TemplateResponse(
        request,
        "public/result.html",
        {
            "business": business,
            "business_slug": slug,
            "service": service,
            "booking": booking,
        },
    )
