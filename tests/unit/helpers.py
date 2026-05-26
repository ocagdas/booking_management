from datetime import time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.enums import ApprovalMode, DurationType, DurationUnit, GapUnit
from app.models.location import LocationWorkingHours
from app.models.service import Service
from app.models.staff import Staff
from app.services.business_service import create_business


def seed_hairdresser(session: Session):
    business = create_business(session, name="Lucknow Hair", slug="lucknow-hair")
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
        name="Asha",
        role="Stylist",
    )
    customer = Customer(
        business_id=business.id,
        name="Mina",
        email="mina@example.test",
        phone="07123456789",
    )
    service = Service(
        business_id=business.id,
        name="Cut",
        duration_type=DurationType.fixed.value,
        fixed_duration_value=30,
        fixed_duration_unit=DurationUnit.minutes.value,
        gap_after_value=0,
        gap_after_unit=GapUnit.minutes.value,
        price=Decimal("25.00"),
        approval_mode=ApprovalMode.auto.value,
    )
    service.locations.append(location)
    session.add_all([staff, customer, service])
    session.commit()
    return business, location, staff, customer, service
