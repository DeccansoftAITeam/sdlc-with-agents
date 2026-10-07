from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.db import system_session

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness: the process is up. Never touches dependencies."""
    return {"status": "ok"}


@router.get("/readyz", response_model=None)
async def readyz() -> dict[str, str] | JSONResponse:
    """Readiness: dependencies reachable. Used by smoke tests and slot swaps."""
    try:
        async with system_session() as s:
            await s.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "unavailable", "db": "down"}, status_code=503)
    return {"status": "ok", "db": "ok"}
