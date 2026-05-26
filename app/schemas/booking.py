from datetime import datetime

from pydantic import BaseModel


class BookingCreate(BaseModel):
    business_id: int
    location_id: int
    service_id: int
    staff_id: int
    customer_id: int
    starts_at: datetime
    selected_duration_value: int | None = None
    selected_duration_unit: str | None = None
    gap_after_value: int | None = None
    gap_after_unit: str | None = None
    notes: str | None = None
