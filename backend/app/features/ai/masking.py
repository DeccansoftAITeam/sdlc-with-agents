"""TD-008/AC-4: mask personal data before any text reaches a model (constitution §2.4).

Deliberately simple and over-eager: masking a harmless number costs a little accuracy;
leaking a card number costs far more. Order matters: cards before phones (a card number
also looks like a long phone number).
"""

import re

# Local part: every RFC 5322 "atext" character (Hypothesis found `/@a.ac`, a valid address).
EMAIL = re.compile(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
# 13-19 digits, optionally separated by single spaces or dashes.
CARD = re.compile(r"(?<!\d)(?:\d[ \-]?){12,18}\d(?!\d)")
# 7-15 digits with common separators, optional leading +.
PHONE = re.compile(r"(?<![\w])\+?\d(?:[\s\-.()]*\d){6,14}(?!\d)")


def mask(text: str) -> str:
    text = EMAIL.sub("[EMAIL]", text)
    text = CARD.sub("[CARD]", text)
    return PHONE.sub("[PHONE]", text)
