from fastapi import FastAPI

from app.api.router import api_router
from app.core.settings import get_settings


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.project_name)
    application.include_router(api_router)
    return application


app = create_application()

