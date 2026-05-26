from decimal import Decimal

from app.models.enums import DurationType, DurationUnit, GapUnit
from app.models.service import Service
from tests.unit.helpers import seed_hairdresser


def test_service_can_link_to_multiple_locations(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    from app.models.location import Location

    second = Location(business_id=business.id, name="Second branch")
    service.locations.append(second)
    db_session.add(second)
    db_session.commit()

    assert {loc.name for loc in service.locations} == {"Default location", "Second branch"}


def test_hidden_duration_flags_are_persisted(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.hide_duration_from_customer = True
    service.hide_duration_completely = True
    db_session.commit()

    found = db_session.get(Service, service.id)

    assert found.hide_duration_from_customer is True
    assert found.hide_duration_completely is True


def test_admin_defined_service_model_fields(db_session):
    business, location, staff, customer, service = seed_hairdresser(db_session)
    service.duration_type = DurationType.admin_defined.value
    service.admin_duration_value = 1
    service.admin_duration_unit = DurationUnit.hours.value
    service.gap_after_value = 10
    service.gap_after_unit = GapUnit.minutes.value
    service.price = Decimal("45.00")
    db_session.commit()

    found = db_session.get(Service, service.id)

    assert found.admin_duration_value == 1
    assert found.admin_duration_unit == "hours"
