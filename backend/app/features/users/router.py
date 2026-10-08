"""HTTP routes for TD-002. No business logic here (AGENTS.md)."""

import uuid

from fastapi import APIRouter, Request, status

from app.features.users import service
from app.features.users.deps import Admin
from app.features.users.schemas import RegisterIn, UserCreateIn, UserOut, UserPatchIn

router = APIRouter(tags=["users"])


def _out(user: object) -> UserOut:
    return UserOut.model_validate(user, from_attributes=True)


@router.post("/t/{slug}/auth/register", status_code=status.HTTP_201_CREATED)
async def register(slug: str, body: RegisterIn, request: Request) -> UserOut:
    ip = request.client.host if request.client else "unknown"
    return _out(await service.register_customer(slug, body, ip))


@router.post("/t/{slug}/users", status_code=status.HTTP_201_CREATED)
async def create_user(slug: str, body: UserCreateIn, admin: Admin) -> UserOut:
    return _out(await service.create_account(admin, body))


@router.get("/t/{slug}/users")
async def list_users(slug: str, admin: Admin) -> list[UserOut]:
    return [_out(u) for u in await service.list_users(admin)]


@router.patch("/t/{slug}/users/{user_id}")
async def update_user(slug: str, user_id: uuid.UUID, body: UserPatchIn, admin: Admin) -> UserOut:
    return _out(await service.update_user(admin, user_id, body))
