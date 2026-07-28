import re
import warnings

import pytest
from fastapi import FastAPI
from starlette.exceptions import StarletteDeprecationWarning

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated",
    category=StarletteDeprecationWarning,
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from backend.config import Config
from backend.database.connection import Base, get_db
from backend.routes.accounts import dashboard_router, router as accounts_router
from backend.routes.admin import router as admin_router
from backend.routes.hub import router as hub_router
from backend.routes.transporter import router as transporter_router


def test_database_url():
    configured_url = make_url(Config.get_database_url())
    explicit_url = __import__("os").getenv("TEST_DATABASE_URL")
    url = make_url(explicit_url) if explicit_url else configured_url.set(database="freshlink_test")

    if not url.database or not url.database.endswith("_test"):
        raise RuntimeError("Integration tests require a PostgreSQL database ending in '_test'.")
    if not re.fullmatch(r"[A-Za-z0-9_]+", url.database):
        raise RuntimeError("The integration test database name contains unsupported characters.")
    return url


def ensure_test_database(url):
    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": url.database},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def integration_engine():
    url = test_database_url()
    ensure_test_database(url)
    engine = create_engine(url, pool_pre_ping=True, poolclass=NullPool)

    # Importing the model package registers every table with SQLAlchemy metadata.
    import backend.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(integration_engine):
    Base.metadata.drop_all(bind=integration_engine)
    Base.metadata.create_all(bind=integration_engine)
    session = sessionmaker(bind=integration_engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def api_client(db_session):
    application = FastAPI()
    application.include_router(accounts_router)
    application.include_router(admin_router)
    application.include_router(hub_router)
    application.include_router(transporter_router)
    application.include_router(dashboard_router)

    def override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture()
def provider_payload():
    def build(role, suffix):
        base = {
            "role": role,
            "username": f"provider_{suffix}",
            "email": f"provider_{suffix}@example.com",
            "password": "FreshLink!123",
            "confirm_password": "FreshLink!123",
            "name": f"Provider {suffix}",
            "phone": f"0788000{suffix:03d}",
            "district": "Kamonyi",
            "sector": "Runda",
            "cell": "Gacurabwenge",
            "village": "Kigusa",
        }
        if role == "truck_provider":
            base.update({"plate_number": f"RAA {suffix:03d}A", "capacity_kg": 1000})
        else:
            base.update({"total_capacity_kg": 2000})
        return base

    return build
