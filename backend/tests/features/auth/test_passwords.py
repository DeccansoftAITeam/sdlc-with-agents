"""Unit tests for the password module (TD-001/AC-3 support; ADR-0002)."""

import hashlib
from typing import Any

import httpx
import pytest

from app.core.errors import ProblemError
from app.features.auth.passwords import HibpRangeChecker, enforce_policy, hash_password, verify_password

PW = "a-long-unique-passphrase"
SUFFIX = hashlib.sha1(PW.encode(), usedforsecurity=False).hexdigest().upper()[5:]


def _checker(body: str = "", status: int = 200, fail: bool = False) -> HibpRangeChecker:
    def handler(request: httpx.Request) -> httpx.Response:
        if fail:
            raise httpx.ConnectError("down", request=request)
        assert len(request.url.path.rsplit("/", 1)[1]) == 5  # only the 5-char prefix leaves
        return httpx.Response(status, text=body)

    return HibpRangeChecker(transport=httpx.MockTransport(handler))


def test_hash_is_argon2id_and_verifies() -> None:
    h = hash_password(PW)
    assert h.startswith("$argon2id$")
    assert verify_password(h, PW) and not verify_password(h, "wrong-password-123")
    assert not verify_password("not-a-hash", PW)


async def test_hibp_match_means_breached() -> None:
    assert await _checker(f"00000:1\n{SUFFIX}:42\n").is_breached(PW)


async def test_hibp_no_match_means_not_breached() -> None:
    assert not await _checker("00000:1\n").is_breached(PW)


@pytest.mark.parametrize("kw", [{"fail": True}, {"status": 503}])
async def test_hibp_outage_fails_open(kw: dict[str, Any]) -> None:
    assert not await _checker(**kw).is_breached(PW)


async def test_policy_rejects_over_max_length() -> None:
    with pytest.raises(ProblemError):
        await enforce_policy("x" * 129, _checker())
