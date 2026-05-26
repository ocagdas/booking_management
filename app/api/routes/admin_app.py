from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.service import Service
from app.services.availability_service import available_start_times

router = APIRouter(prefix="/admin/app", tags=["admin-app"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/availability/slots", response_class=HTMLResponse)
def availability_slots(
    request: Request,
    business_id: int,
    location_id: int,
    staff_id: int,
    service_id: int,
    day: date,
    selected_duration_value: int | None = Query(default=None),
    selected_duration_unit: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    service = db.get(Service, service_id)
    slots = []
    if service is not None:
        slots = available_start_times(
            db,
            business_id=business_id,
            location_id=location_id,
            staff_id=staff_id,
            service=service,
            day=day,
            selected_duration_value=selected_duration_value,
            selected_duration_unit=selected_duration_unit,
        )
    return templates.TemplateResponse(
        request,
        "fragments/available_slots.html",
        {"slots": slots},
    )
