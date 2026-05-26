from fastapi import APIRouter

from app.api.routes.admin_app import router as admin_app_router
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(admin_app_router)
