"""HTTP routes for TD-001 signup and sessions. No business logic here (AGENTS.md)."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.core.config import get_settings
from app.core.security import ACCESS_TTL_SECONDS, Principal, current_principal
from app.features.auth import service, sessions
from app.features.auth.schemas import LoginIn, MeOut, SignupIn, SignupOut, TokenOut

router = APIRouter(tags=["auth"])
COOKIE = "refresh_token"
RefreshCookie = Annotated[str | None, Cookie(alias=COOKIE)]


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _issue(response: Response, slug: str, tokens: sessions.Tokens) -> TokenOut:
    response.set_cookie(
        COOKIE,
        tokens.refresh,
        max_age=sessions.REFRESH_TTL_DAYS * 24 * 3600,
        path=f"{get_settings().cookie_path_prefix}/t/{slug}/auth",
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return TokenOut(access_token=tokens.access, expires_in=ACCESS_TTL_SECONDS)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn, request: Request) -> SignupOut:
    return SignupOut(tenant_slug=await service.signup(body, _ip(request)))


@router.post("/t/{slug}/auth/login")
async def login(slug: str, body: LoginIn, request: Request, response: Response) -> TokenOut:
    return _issue(response, slug, await sessions.login(slug, body.email, body.password, _ip(request)))


@router.post("/t/{slug}/auth/refresh")
async def refresh(slug: str, response: Response, refresh_token: RefreshCookie = None) -> TokenOut:
    return _issue(response, slug, await sessions.refresh(slug, refresh_token))


@router.post("/t/{slug}/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(slug: str, refresh_token: RefreshCookie = None) -> Response:
    await sessions.logout(slug, refresh_token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE, path=f"{get_settings().cookie_path_prefix}/t/{slug}/auth")
    return response


@router.get("/t/{slug}/me")
async def me(slug: str, principal: Annotated[Principal, Depends(current_principal)]) -> MeOut:
    user = await sessions.me(principal)
    return MeOut(id=str(user.id), email=user.email, name=user.name, role=user.role, tenant_slug=slug)
