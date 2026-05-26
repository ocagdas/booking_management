from sqlalchemy import String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Business(TimestampMixin, Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    locations: Mapped[list["Location"]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
    )
    staff_members: Mapped[list["Staff"]] = relationship(back_populates="business")
    services: Mapped[list["Service"]] = relationship(back_populates="business")
    customers: Mapped[list["Customer"]] = relationship(back_populates="business")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="business")

    def __str__(self) -> str:
        return self.name


@event.listens_for(Business, "after_insert")
def create_default_location(mapper, connection, target: Business) -> None:
    from app.models.location import Location

    connection.execute(
        Location.__table__.insert().values(
            business_id=target.id,
            name="Default location",
            is_default=True,
        )
    )
