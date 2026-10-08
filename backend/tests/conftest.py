"""Test fixtures. Requires the local database: `docker compose up -d db`.

The schema is migrated once per session as the OWNER role; tests then talk to
the database as the APP role, exactly like production, so RLS is really enforced.
"""

import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.main import create_app

if TYPE_CHECKING:
    from app.core.email import InMemoryOutbox

BACKEND = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, check=True)


@pytest.fixture(scope="session")
async def owner_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(get_settings().migration_database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def app_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(get_settings().database_url)
    yield engine
    await engine.dispose()


class FakeBreachChecker:
    """Deterministic stand-in for the HIBP range API; tests never call the network."""

    breached = frozenset({"password1234", "correcthorsebatterystaple"})

    async def is_breached(self, password: str) -> bool:
        return password.lower() in self.breached


@pytest.fixture
def outbox() -> "InMemoryOutbox":
    from app.core.email import InMemoryOutbox

    return InMemoryOutbox()


@pytest.fixture
def app(outbox: "InMemoryOutbox") -> FastAPI:
    from app.core.email import get_email_sender
    from app.features.auth.passwords import get_breach_checker

    application = create_app()
    application.dependency_overrides[get_email_sender] = lambda: outbox
    application.dependency_overrides[get_breach_checker] = FakeBreachChecker
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
