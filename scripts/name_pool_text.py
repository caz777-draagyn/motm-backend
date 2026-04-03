"""
Shared text rules for name-pool build scripts.

- canon_name: NFKC + title case; preserves Latin diacritics (macrons, accents).
- is_plausible_token: Unicode Latin letters only (not ASCII-only), plus ' . ` in parts.

Run scripts as `python scripts/foo.py`; import path is adjusted in each caller.
"""

from __future__ import annotations

import re
import unicodedata


def canon_name(raw: str) -> str:
    """NFKC, title-case each space/hyphen chunk; keeps combining Latin letters."""
    base = unicodedata.normalize("NFKC", (raw or "").strip()).replace("–", "-")
    words: list[str] = []
    for w in base.split():
        parts = [p for p in w.split("-") if p.strip()]
        if not parts:
            continue
        words.append("-".join(p[:1].upper() + p[1:].lower() if p else p for p in parts))
    return " ".join(words)


def is_latin_letter_char(c: str) -> bool:
    if len(c) != 1:
        return False
    try:
        return unicodedata.name(c).startswith("LATIN")
    except ValueError:
        return False


def is_plausible_token(s: str) -> bool:
    """Latin script letters (Unicode LATIN* names); allows ' . `; rejects digits."""
    if not s or len(s) < 2:
        return False
    if any(ch.isdigit() for ch in s):
        return False
    for part in re.split(r"[\s-]", s):
        if not part:
            continue
        part = unicodedata.normalize("NFC", part)
        for c in part:
            if c in "'.`":
                continue
            if not is_latin_letter_char(c):
                return False
    return True
