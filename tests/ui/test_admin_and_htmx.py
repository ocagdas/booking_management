from datetime import time
from decimal import Decimal

from bs4 import BeautifulSoup

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.enums import ApprovalMode, DurationType, DurationUnit, GapUnit
from app.models.location import LocationWorkingHours
from app.models.service import Service
from app.models.staff import Staff
from app.services.business_service import create_business


def _seed_app_db():
    with SessionLocal() as session:
        business = create_business(session, name="Admin Salon", slug="admin-salon")
        location = business.locations[0]
        session.add(
            LocationWorkingHours(
                location_id=location.id,
                day_of_week=0,
                opens_at=time(9, 0),
                closes_at=time(17, 0),
                is_closed=False,
            )
        )
        staff = Staff(
            business_id=business.id,
            location_id=location.id,
            name="Rina",
            role="Stylist",
        )
        customer = Customer(business_id=business.id, name="Leela")
        service = Service(
            business_id=business.id,
            name="Trim",
            duration_type=DurationType.fixed.value,
            fixed_duration_value=30,
            fixed_duration_unit=DurationUnit.minutes.value,
            gap_after_value=0,
            gap_after_unit=GapUnit.minutes.value,
            price=Decimal("20.00"),
            approval_mode=ApprovalMode.auto.value,
        )
        service.locations.append(location)
        session.add_all([staff, customer, service])
        session.commit()
        return business.id, location.id, staff.id, service.id


def test_sqladmin_loads(client):
    response = client.get("/admin/sql/")

    assert response.status_code == 200
    assert "Booking Admin" in response.text


def test_service_create_form_uses_selects_and_multiselect(client):
    response = client.get("/admin/sql/service/create")

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find("select", {"name": "business"}) is not None
    assert soup.find("select", {"name": "duration_type"}) is not None
    locations = soup.find("select", {"name": "locations"})
    assert locations is not None
    assert locations.has_attr("multiple")


def test_htmx_slots_fragment_returns_dropdown_options(client):
    business_id, location_id, staff_id, service_id = _seed_app_db()

    response = client.get(
        "/admin/app/availability/slots",
        params={
            "business_id": business_id,
            "location_id": location_id,
            "staff_id": staff_id,
            "service_id": service_id,
            "day": "2026-06-01",
        },
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find("select", {"name": "starts_at"}) is not None
    assert soup.find("option", string="09:00") is not None
