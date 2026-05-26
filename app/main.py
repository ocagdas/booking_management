from fastapi import FastAPI

from app.admin.sqladmin.setup import setup_sqladmin
from app.api.router import api_router
from app.core.settings import get_settings


def create_application() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.project_name)
    app.include_router(api_router)
    setup_sqladmin(app)
    return app


app = create_application()
