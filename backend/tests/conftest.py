"""Test configuration. See docs/testing.md for the strategy."""

import os
from pathlib import Path

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.exc import OperationalError

BACKEND_DIR = Path(__file__).resolve().parent.parent


class DatabaseTestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    test_database_url: str


TEST_DATABASE_URL = make_url(DatabaseTestSettings().test_database_url)

# Never run against a database that could hold real data: it is dropped below.
if not TEST_DATABASE_URL.database or not TEST_DATABASE_URL.database.endswith("_test"):
    raise pytest.UsageError(
        f"TEST_DATABASE_URL must name a database ending in _test, "
        f"got {TEST_DATABASE_URL.database!r}."
    )

# Point the application at the test database before any app module is imported.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL.render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def database():
    """Recreate the test database and apply all migrations, once per session."""
    from alembic import command
    from alembic.config import Config

    admin_engine = create_engine(
        TEST_DATABASE_URL.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        # Without a timeout, an unreachable server can hang instead of failing.
        connect_args={"connect_timeout": 3},
    )
    name = TEST_DATABASE_URL.database
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            connection.execute(text(f'CREATE DATABASE "{name}"'))
    except OperationalError as error:
        pytest.exit(
            f"Cannot reach PostgreSQL for the test database ({error.orig}). "
            "Start it from the repository root with: docker compose up -d --wait db",
            returncode=1,
        )
    finally:
        admin_engine.dispose()

    command.upgrade(Config(BACKEND_DIR / "alembic.ini"), "head")


@pytest.fixture
def client(database):
    """API client. Expenses created by the test are removed afterwards."""
    from fastapi.testclient import TestClient

    from app.core.db import engine
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    # Seed data (users, groups, memberships) is never modified, so it is kept.
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE expense_shares, expenses RESTART IDENTITY"))
