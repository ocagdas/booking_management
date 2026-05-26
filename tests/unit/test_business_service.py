from app.models.location import Location
from app.services.business_service import create_business, default_location_for_business


def test_create_business_creates_default_location(db_session):
    business = create_business(db_session, name="Salon One", slug="salon-one")

    locations = db_session.query(Location).filter_by(business_id=business.id).all()
    assert len(locations) == 1
    assert locations[0].name == "Default location"
    assert locations[0].is_default is True


def test_default_location_for_business_returns_only_location(db_session):
    business = create_business(db_session, name="Salon Two", slug="salon-two")

    location = default_location_for_business(db_session, business.id)

    assert location is not None
    assert location.business_id == business.id
