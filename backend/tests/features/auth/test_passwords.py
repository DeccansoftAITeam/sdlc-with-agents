"""Unit tests for the password module (TD-001/AC-3 support; ADR-0002 as amended)."""

import pytest

from app.core.errors import ProblemError
from app.features.auth.passwords import common_passwords, enforce_policy, hash_password, verify_password

PW = "a-long-unique-passphrase"


def test_hash_is_argon2id_and_verifies() -> None:
    h = hash_password(PW)
    assert h.startswith("$argon2id$")
    assert verify_password(h, PW) and not verify_password(h, "wrong-password-123")
    assert not verify_password("not-a-hash", PW)


def test_password_is_unicode_normalised() -> None:
    """'ﬁ' (ligature) and 'fi' must be the same passphrase."""
    h = hash_password("my ﬁne long passphrase")
    assert verify_password(h, "my fine long passphrase")


def test_common_list_is_bundled_and_lowercase() -> None:
    words = common_passwords()
    assert len(words) > 40
    assert all(w == w.lower() and not w.startswith("#") for w in words)


def test_policy_accepts_a_good_passphrase() -> None:
    enforce_policy(PW)


@pytest.mark.parametrize("pw", ["x" * 11, "x" * 129, "Password1234"])
def test_policy_rejects(pw: str) -> None:
    with pytest.raises(ProblemError):
        enforce_policy(pw)
