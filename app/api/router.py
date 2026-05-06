from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.public_booking import router as public_booking_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(bookings_router)
api_router.include_router(public_booking_router)

