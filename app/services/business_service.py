from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.location import Location


def create_business(session: Session, *, name: str, slug: str) -> Business:
    business = Business(name=name, slug=slug)
    session.add(business)
    session.commit()
    session.refresh(business)
    return business


def default_location_for_business(session: Session, business_id: int) -> Location | None:
    default_location = session.scalar(
        select(Location)
        .where(Location.business_id == business_id, Location.is_default.is_(True))
        .order_by(Location.id)
    )
    if default_location is not None:
        return default_location

    locations = session.scalars(
        select(Location).where(Location.business_id == business_id).order_by(Location.id)
    ).all()
    if len(locations) == 1:
        return locations[0]
    return None
