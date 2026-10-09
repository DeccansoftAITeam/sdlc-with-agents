"""Admin routes for per-tenant feature flags. No business logic here (AGENTS.md)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.features.flags import service
from app.features.users.deps import Admin

router = APIRouter(tags=["flags"])


class FlagIn(BaseModel):
    enabled: bool


@router.get("/t/{slug}/flags")
async def list_flags(slug: str, admin: Admin) -> dict[str, bool]:
    return await service.get_all(admin)


@router.put("/t/{slug}/flags/{key}")
async def set_flag(slug: str, key: str, body: FlagIn, admin: Admin) -> dict[str, bool]:
    await service.set_flag(admin, key, body.enabled)
    return await service.get_all(admin)
