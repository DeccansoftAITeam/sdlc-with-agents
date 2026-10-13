"""TD-008/AC-4: emails, phone numbers and card-like numbers never reach the model."""

import re

from hypothesis import given
from hypothesis import strategies as st

from app.features.ai.masking import mask

words = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Zs")), max_size=40)
emails = st.emails().map(str)
cards = st.lists(st.integers(0, 9), min_size=13, max_size=19).map(lambda ds: "".join(map(str, ds)))
spaced_cards = st.from_regex(r"\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}", fullmatch=True)
phones = st.from_regex(r"\+?\d{1,3}[ \-]?\(?\d{3}\)?[ \-]?\d{3}[ \-]?\d{4}", fullmatch=True)


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


@given(words, emails, words)
def test_td008_ac4_emails_are_masked(before: str, email: str, after: str) -> None:
    out = mask(f"{before} {email} {after}")
    assert email not in out
    assert "[EMAIL]" in out


@given(words, st.one_of(cards, spaced_cards, phones), words)
def test_td008_ac4_card_and_phone_numbers_are_masked(before: str, number: str, after: str) -> None:
    out = mask(f"{before} {number} {after}")
    assert _digits(number) not in _digits(out)  # no run of the original digits survives


def test_td008_ac4_ordinary_text_is_kept() -> None:
    text = "Order 4521 failed twice since version 2.3, see ticket #88"
    assert mask(text) == text  # short numbers carry meaning for triage


def test_td008_ac4_examples() -> None:
    assert mask("Mail ada@example.com or call +1 (555) 010-9999") == "Mail [EMAIL] or call [PHONE]"
    assert mask("Card 4111 1111 1111 1111 was charged") == "Card [CARD] was charged"
