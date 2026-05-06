"""Lightweight internal API used by admin UI JS (e.g. ends_at auto-fill)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.service import Service

router = APIRouter(prefix="/admin/api", tags=["admin-api"])


@router.get("/services/{service_id}")
def service_info(service_id: int, db: Session = Depends(get_db_session)):
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"id": service.id, "duration_minutes": service.duration_minutes}
