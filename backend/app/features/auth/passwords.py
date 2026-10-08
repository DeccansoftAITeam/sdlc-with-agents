"""Password hashing and policy (ADR-0002, ASVS L2 V2.1, TD-001/AC-3).

- Argon2id via argon2-cffi defaults (RFC 9106 profile).
- Minimum 12 characters, maximum 128; no composition rules (they lower real security).
- Breached-password check through the HIBP k-anonymity range API: only the first five
  hex characters of the SHA-1 hash leave the process. Fails open (with a log line) so an
  outage of a third party can't block signup.
"""

import hashlib
import logging
from typing import Protocol

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.errors import ProblemError

log = logging.getLogger(__name__)
_hasher = PasswordHasher()

MIN_LENGTH = 12
MAX_LENGTH = 128


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


class BreachedPasswordChecker(Protocol):
    async def is_breached(self, password: str) -> bool: ...


class HibpRangeChecker:
    URL = "https://api.pwnedpasswords.com/range/{prefix}"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport  # injectable for tests; never hit the network in CI

    async def is_breached(self, password: str) -> bool:
        digest = hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        try:
            async with httpx.AsyncClient(timeout=2.0, transport=self._transport) as client:
                r = await client.get(self.URL.format(prefix=prefix), headers={"Add-Padding": "true"})
                r.raise_for_status()
        except httpx.HTTPError:
            log.warning("breached-password check unavailable; failing open")
            return False
        return any(line.split(":", 1)[0] == suffix for line in r.text.splitlines())


def get_breach_checker() -> BreachedPasswordChecker:
    return HibpRangeChecker()


async def enforce_policy(password: str, checker: BreachedPasswordChecker) -> None:
    if not MIN_LENGTH <= len(password) <= MAX_LENGTH:
        raise ProblemError(422, "Weak password", f"Use {MIN_LENGTH} to {MAX_LENGTH} characters.")
    if await checker.is_breached(password):
        raise ProblemError(
            422, "Weak password", "This password appears in a known data breach. Choose another."
        )
