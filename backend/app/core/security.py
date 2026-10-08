"""Access tokens and the request principal (ADR-0002, ADR-0003, TD-001/AC-4, AC-12).

- Access token: JWT signed with Ed25519 ("EdDSA"), 15 minutes, claims sub/tid/role/jti/iat/exp.
  Verification pins the algorithm, so "alg: none" or HS256 tricks are rejected.
- `current_principal` is the dependency every tenant route uses. The tenant comes from
  the token; the URL slug must resolve to the SAME tenant, otherwise 404 (grill Q3).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Annotated

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from fastapi import Header
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import system_session
from app.core.errors import ProblemError

ACCESS_TTL_SECONDS = 900
ALGORITHM = "EdDSA"
UNAUTHENTICATED = ProblemError(401, "Unauthorized", "Missing, invalid or expired access token.")
NOT_FOUND = ProblemError(404, "Not Found")


@lru_cache
def _signing_key() -> Ed25519PrivateKey:
    settings = get_settings()
    if settings.jwt_private_key_pem:
        key = load_pem_private_key(settings.jwt_private_key_pem.encode(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise RuntimeError("jwt_private_key_pem must be an Ed25519 key")
        return key
    if settings.environment == "local":
        # Ephemeral: tokens stop validating on restart. Never used outside local.
        return Ed25519PrivateKey.generate()
    raise RuntimeError("jwt_private_key_pem is required outside environment=local")


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str


def issue_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID, role: str) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ACCESS_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(claims, _signing_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> Principal:
    try:
        claims = jwt.decode(
            token,
            _signing_key().public_key(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "tid", "role", "jti", "iat", "exp"]},
        )
        return Principal(uuid.UUID(claims["sub"]), uuid.UUID(claims["tid"]), str(claims["role"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise UNAUTHENTICATED from None


async def resolve_tenant(slug: str) -> uuid.UUID:
    """Slug -> tenant id via the SECURITY DEFINER function; unknown slug -> 404."""
    async with system_session() as s:
        tid = (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one()
    if tid is None:
        raise NOT_FOUND
    return uuid.UUID(str(tid))


async def current_principal(slug: str, authorization: Annotated[str | None, Header()] = None) -> Principal:
    """FastAPI dependency for routes under /t/{slug}/…"""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UNAUTHENTICATED
    principal = decode_access_token(token)
    if await resolve_tenant(slug) != principal.tenant_id:
        raise NOT_FOUND  # TD-001/AC-12: don't reveal that the tenant exists
    return principal
