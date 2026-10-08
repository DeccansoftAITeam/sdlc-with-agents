"""HTTP routes for TD-001 signup. No business logic here (AGENTS.md)."""

from fastapi import APIRouter, status

from app.features.auth import service
from app.features.auth.schemas import SignupIn, SignupOut

router = APIRouter(tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn) -> SignupOut:
    return SignupOut(tenant_slug=await service.signup(body))
