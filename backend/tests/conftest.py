"""Test fixtures. Requires the local database: `docker compose up -d db`.

The schema is migrated once per session as the OWNER role; tests then talk to
the database as the APP role, exactly like production, so RLS is really enforced.
"""

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

# Must be set before the app is imported: the app checks its signing key at startup.
os.environ.setdefault("JWT_EPHEMERAL_KEY", "true")  # tests sign with an in-memory key

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.main import create_app

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


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    """Rate-limit state is process-wide; every test starts with a clean slate."""
    try:
        from app.core import ratelimit
    except ImportError:  # before T-001-03 exists
        return
    ratelimit.reset()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
