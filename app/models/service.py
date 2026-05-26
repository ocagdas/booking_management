from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import service_locations
from app.models.base import Base, TimestampMixin
from app.models.enums import ApprovalMode, DurationType, DurationUnit, GapUnit


class Service(TimestampMixin, Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    duration_type: Mapped[str] = mapped_column(
        String(40),
        default=DurationType.fixed.value,
        nullable=False,
    )
    fixed_duration_value: Mapped[int | None] = mapped_column(nullable=True)
    fixed_duration_unit: Mapped[str | None] = mapped_column(
        String(20),
        default=DurationUnit.minutes.value,
        nullable=True,
    )
    variable_min_duration_value: Mapped[int | None] = mapped_column(nullable=True)
    variable_min_duration_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    variable_max_duration_value: Mapped[int | None] = mapped_column(nullable=True)
    variable_max_duration_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    variable_increment_value: Mapped[int | None] = mapped_column(nullable=True)
    variable_increment_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    admin_duration_value: Mapped[int | None] = mapped_column(nullable=True)
    admin_duration_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)

    hide_duration_from_customer: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    hide_duration_completely: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    gap_after_value: Mapped[int] = mapped_column(default=0, nullable=False)
    gap_after_unit: Mapped[str] = mapped_column(
        String(20),
        default=GapUnit.minutes.value,
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    approval_mode: Mapped[str] = mapped_column(
        String(20),
        default=ApprovalMode.auto.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship(back_populates="services")
    locations: Mapped[list["Location"]] = relationship(
        secondary=service_locations,
        back_populates="services",
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")

    def __str__(self) -> str:
        return self.name
