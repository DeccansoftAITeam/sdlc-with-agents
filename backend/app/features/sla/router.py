"""HTTP routes for TD-005 (admin only). No business logic here (AGENTS.md)."""

from fastapi import APIRouter

from app.features.sla import service
from app.features.sla.schemas import SlaSettingsIO
from app.features.users.deps import Admin

router = APIRouter(tags=["sla"])


@router.get("/t/{slug}/sla-settings")
async def get_sla_settings(slug: str, admin: Admin) -> SlaSettingsIO:
    return SlaSettingsIO.model_validate(await service.get_settings(admin))


@router.put("/t/{slug}/sla-settings")
async def put_sla_settings(slug: str, body: SlaSettingsIO, admin: Admin) -> SlaSettingsIO:
    return SlaSettingsIO.model_validate(await service.put_settings(admin, body))
