from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import BookingStatus, DurationUnit, GapUnit


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    selected_duration_value: Mapped[int] = mapped_column(nullable=False)
    selected_duration_unit: Mapped[str] = mapped_column(
        String(20),
        default=DurationUnit.minutes.value,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gap_after_value: Mapped[int] = mapped_column(default=0, nullable=False)
    gap_after_unit: Mapped[str] = mapped_column(
        String(20),
        default=GapUnit.minutes.value,
        nullable=False,
    )
    blocked_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=BookingStatus.pending_approval.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    business: Mapped["Business"] = relationship(back_populates="bookings")
    location: Mapped["Location"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    staff: Mapped["Staff"] = relationship(back_populates="bookings")
    customer: Mapped["Customer"] = relationship(back_populates="bookings")

    def __str__(self) -> str:
        return f"{self.service} for {self.customer} at {self.starts_at}"
