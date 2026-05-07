"""Public booking page routes — Jinja2 + HTMX server-rendered flow."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db_session
from app.models.booking import BookingStatus
from app.models.business import Business, Location
from app.models.customer import Customer
from app.models.resource import Resource
from app.models.service import Service, PriceUnit, calculate_amount_due
from app.models.service_extra import ServiceExtra
from app.models.staff import Staff
from app.schemas.booking import BookingCreateRequest
from app.services import availability_service, booking_service

router = APIRouter(prefix="/book", tags=["public"])
templates = Jinja2Templates(directory="app/templates")

_UTC = timezone.utc
_SLOT_HOURS = list(range(8, 18))  # 08:00–17:00 on the hour

# Minutes per price-unit billing period — used for cost display in templates.
_PRICE_UNIT_MINUTES: dict[str, int] = {
    PriceUnit.per_minute.value: 1,
    PriceUnit.per_5_min.value: 5,
    PriceUnit.per_15_min.value: 15,
    PriceUnit.per_30_min.value: 30,
    PriceUnit.per_hour.value: 60,
}


def _get_business(slug: str, db: Session) -> Business:
    business = db.scalar(select(Business).where(Business.slug == slug))
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


def _build_location_groups(
    business_id: int,
    db: Session,
    service_staff: list | None = None,
    service_resources: list | None = None,
) -> list[dict]:
    """Return a list of location dicts with active staff and resources.

    Each entry has the shape::

        {"location": Location, "staff": [Staff, ...], "resources": [Resource, ...]}

    Only locations that have at least one active staff member or resource are
    included.  Staff and resources not assigned to any location are **not**
    shown in the public booking flow.
    """
    locations = db.scalars(
        select(Location)
        .where(Location.business_id == business_id)
        .options(
            selectinload(Location.staff_members),
            selectinload(Location.resources),
        )
        .order_by(Location.name)
    ).all()

    # Determine the full set of available staff and resources.
    if service_staff is not None:
        all_staff = list(service_staff)
    else:
        all_staff = list(
            db.scalars(
                select(Staff)
                .where(Staff.business_id == business_id, Staff.is_active.is_(True))
                .order_by(Staff.name)
            ).all()
        )

    if service_resources is not None:
        all_resources = list(service_resources)
    else:
        all_resources = list(
            db.scalars(
                select(Resource)
                .where(Resource.business_id == business_id, Resource.is_active.is_(True))
                .order_by(Resource.name)
            ).all()
        )

    active_staff_ids = {s.id for s in all_staff}
    active_resource_ids = {r.id for r in all_resources}

    groups: list[dict] = []
    for loc in locations:
        loc_staff = [s for s in loc.staff_members if s.id in active_staff_ids]
        loc_resources = [r for r in loc.resources if r.id in active_resource_ids]
        if loc_staff or loc_resources:
            groups.append({"location": loc, "staff": loc_staff, "resources": loc_resources})

    # Unassigned staff/resources are intentionally omitted from the booking UI.
    return groups


def _extras_for_staff(
    service_extras: list[ServiceExtra],
    staff: Staff | None,
) -> list[ServiceExtra]:
    """Filter extras to those the given staff member can offer.

    If *staff* is None or the staff member has no explicit extras assigned,
    all extras are returned (default-all semantics).  This design means that
    small teams where every staff member can offer every extra require no
    extra configuration — the restriction table only needs to be populated
    when a particular staff member's offerings differ from the full list.
    """
    if staff is None or not staff.extras:
        return service_extras
    allowed_ids = {e.id for e in staff.extras}
    return [e for e in service_extras if e.id in allowed_ids]


def _extra_cost(extra: ServiceExtra, duration_minutes: int) -> Decimal:
    """Calculate the cost for one extra given a selected duration."""
    from decimal import ROUND_HALF_UP

    unit_price = Decimal(str(extra.unit_price))
    if extra.price_unit == PriceUnit.flat.value or extra.price_unit == "flat":
        return unit_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    unit_mins = _PRICE_UNIT_MINUTES.get(extra.price_unit, 1)
    units = Decimal(str(duration_minutes)) / Decimal(str(unit_mins))
    return (unit_price * units).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
    service = db.scalar(
        select(Service)
        .where(Service.id == service_id)
        .options(selectinload(Service.resources), selectinload(Service.staff_members))
    )
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")
    today = date.today().isoformat()
    svc_staff = service.staff_members if service.staff_members else None
    svc_resources = service.resources if service.resources else None
    location_groups = _build_location_groups(business.id, db, svc_staff, svc_resources)

    # Resources linked to this service (for the "how many?" picker).
    service_resources = list(service.resources) if service.resources else []

    return templates.TemplateResponse(
        request,
        "public/slot.html",
        {
            "business": business,
            "service": service,
            "today": today,
            "location_groups": location_groups,
            "single_location": len(location_groups) == 1,
            "service_resources": service_resources,
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
    staff_ids: list[int] = Query(default=[]),
    resource_ids: list[int] = Query(default=[]),
    resource_count: int = Query(default=1),
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
                effective_end = ends_at + timedelta(minutes=buffer)

                booked = not availability_service.is_business_slot_available(
                    db,
                    business.id,
                    starts_at,
                    effective_end,
                    staff_ids=staff_ids if staff_ids else None,
                    resource_ids=resource_ids if resource_ids else None,
                    resource_count=max(1, resource_count),
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
# GET /book/{slug}/{service_id}/extras  — HTMX fragment: extras by staff
# ------------------------------------------------------------------
@router.get("/{slug}/{service_id}/extras", response_class=HTMLResponse)
def extras_fragment(
    slug: str,
    service_id: int,
    request: Request,
    staff_id: int | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    """Return an HTMX fragment listing extras filtered by selected staff."""
    business = _get_business(slug, db)
    service = db.scalar(
        select(Service)
        .where(Service.id == service_id)
        .options(selectinload(Service.extras))
    )
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")

    staff: Staff | None = None
    if staff_id:
        staff = db.scalar(
            select(Staff)
            .where(Staff.id == staff_id)
            .options(selectinload(Staff.extras))
        )

    extras = _extras_for_staff(service.extras, staff)
    return templates.TemplateResponse(
        request,
        "public/extras_fragment.html",
        {
            "extras": extras,
            "service_duration": service.duration_minutes,
            "price_unit_minutes": _PRICE_UNIT_MINUTES,
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
    service = db.scalar(
        select(Service)
        .where(Service.id == service_id)
        .options(
            selectinload(Service.extras).selectinload(ServiceExtra.staff_members),
            selectinload(Service.resources),
            selectinload(Service.staff_members).selectinload(Staff.extras),
        )
    )
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        starts_at_dt = datetime.fromisoformat(starts_at.replace(" ", "+"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid starts_at format")
    ends_at_dt = starts_at_dt + timedelta(minutes=service.duration_minutes)

    duration_minutes = service.duration_minutes
    amount_due = calculate_amount_due(service.unit_price, service.price_unit, duration_minutes)

    svc_staff = service.staff_members if service.staff_members else None
    svc_resources = service.resources if service.resources else None
    location_groups = _build_location_groups(business.id, db, svc_staff, svc_resources)

    # All extras for the service (staff filtering happens client-side via HTMX).
    all_extras = list(service.extras)

    return templates.TemplateResponse(
        request,
        "public/details.html",
        {
            "business": business,
            "service": service,
            "starts_at": starts_at_dt,
            "starts_at_iso": starts_at_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "ends_at": ends_at_dt,
            "ends_at_local": ends_at_dt.strftime("%Y-%m-%dT%H:%M"),
            "location_groups": location_groups,
            "single_location": len(location_groups) == 1,
            "extras": all_extras,
            "notes_prompt": service.notes_prompt or "Notes (optional)",
            "amount_due": amount_due,
            "service_duration": duration_minutes,
            "price_unit_minutes": _PRICE_UNIT_MINUTES,
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
    location_id: int | None = Form(None),
    resource_ids: list[int] = Form(default=[]),
    extra_ids: list[int] = Form(default=[]),
    db: Session = Depends(get_db_session),
):
    business = _get_business(slug, db)
    service = db.get(Service, service_id)
    if service is None or service.business_id != business.id:
        raise HTTPException(status_code=404, detail="Service not found")

    try:
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
        location_id=location_id,
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
