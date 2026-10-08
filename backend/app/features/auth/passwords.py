"""Password hashing and policy (ADR-0002 as amended 2026-10-08, ASVS L2 V2.1, TD-001/AC-3).

- Argon2id via argon2-cffi defaults (RFC 9106 profile); NFKC-normalised first.
- 12 to 128 characters; no composition rules (they lower real security).
- Rejected if it appears in the bundled common-password list (offline: the app calls no
  third-party services except the AI gateway).
"""

import unicodedata
from functools import lru_cache
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.errors import ProblemError

_hasher = PasswordHasher()
_COMMON_FILE = Path(__file__).with_name("common_passwords.txt")

MIN_LENGTH = 12
MAX_LENGTH = 128


def normalise(password: str) -> str:
    """NFKC, so the same passphrase typed on different keyboards hashes the same."""
    return unicodedata.normalize("NFKC", password)


def hash_password(password: str) -> str:
    return _hasher.hash(normalise(password))


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, normalise(password))
    except (VerificationError, InvalidHashError):
        return False


@lru_cache
def common_passwords() -> frozenset[str]:
    lines = _COMMON_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(x.strip().lower() for x in lines if x.strip() and not x.startswith("#"))


def enforce_policy(password: str) -> None:
    password = normalise(password)
    if not MIN_LENGTH <= len(password) <= MAX_LENGTH:
        raise ProblemError(422, "Weak password", f"Use {MIN_LENGTH} to {MAX_LENGTH} characters.")
    if password.lower() in common_passwords():
        raise ProblemError(422, "Weak password", "This password is too common. Choose another.")
