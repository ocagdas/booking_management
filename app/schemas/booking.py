"""Pydantic v2 schemas for booking API."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.booking import BookingStatus


class BookingCreateRequest(BaseModel):
    business_id: int
    service_id: int
    customer_id: int
    location_id: int | None = None
    starts_at: datetime
    ends_at: datetime
    resource_ids: list[int] = []
    staff_ids: list[int] = []
    extra_ids: list[int] = []
    notes: str | None = None

    @field_validator("ends_at")
    @classmethod
    def ends_after_starts(cls, v: datetime, info) -> datetime:
        starts_at = info.data.get("starts_at")
        if starts_at is not None and v <= starts_at:
            raise ValueError("ends_at must be after starts_at")
        return v


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    service_id: int
    customer_id: int
    location_id: int | None
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    notes: str | None
    amount_due: Decimal | None


class BookingActionRequest(BaseModel):
    actor: str | None = None
    reason: str | None = None
