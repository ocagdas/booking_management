import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("ZMART_BOOKING_DATABASE_URL_OVERRIDE", "sqlite:///./.test_app.db")

import app.models  # noqa: E402,F401
from app.core.database import engine as app_engine
from app.main import app
from app.models.base import Base


@pytest.fixture(scope="session", autouse=True)
def app_database():
    Base.metadata.drop_all(app_engine)
    Base.metadata.create_all(app_engine)
    yield
    Base.metadata.drop_all(app_engine)
    Path(".test_app.db").unlink(missing_ok=True)


@pytest.fixture(scope="session")
def client(app_database):
    return TestClient(app)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
