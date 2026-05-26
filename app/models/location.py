from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    business: Mapped["Business"] = relationship(back_populates="locations")
    working_hours: Mapped[list["LocationWorkingHours"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
    )
    breaks: Mapped[list["LocationBreak"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
    )
    staff_members: Mapped[list["Staff"]] = relationship(back_populates="location")
    services: Mapped[list["Service"]] = relationship(
        secondary="service_locations",
        back_populates="locations",
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="location")

    __table_args__ = (UniqueConstraint("business_id", "name", name="uq_location_business_name"),)

    def __str__(self) -> str:
        return f"{self.business.name} - {self.name}" if self.business else self.name


class LocationWorkingHours(Base):
    __tablename__ = "location_working_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    opens_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    closes_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    location: Mapped[Location] = relationship(back_populates="working_hours")

    __table_args__ = (
        UniqueConstraint("location_id", "day_of_week", name="uq_location_hours_day"),
    )

    def __str__(self) -> str:
        status = "closed" if self.is_closed else f"{self.opens_at}-{self.closes_at}"
        return f"{self.location} day {self.day_of_week}: {status}"


class LocationBreak(Base):
    __tablename__ = "location_breaks"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_at: Mapped[time] = mapped_column(Time, nullable=False)
    ends_at: Mapped[time] = mapped_column(Time, nullable=False)

    location: Mapped[Location] = relationship(back_populates="breaks")

    def __str__(self) -> str:
        return f"{self.location} day {self.day_of_week}: {self.starts_at}-{self.ends_at}"
