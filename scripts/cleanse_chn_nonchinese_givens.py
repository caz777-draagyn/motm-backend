#!/usr/bin/env python3
"""
Keep only Han-Chinese-style romanized given names in country_CHN given_names_male.

Uses greedy segmentation against Mandarin pinyin syllables (from Han coverage via
pypinyin; stored in data/chinese_pinyin_syllables.txt — regenerate with
scripts/_build_pinyin_syllables.py after pip install pypinyin).

Drops syllables {a, m, n} that are valid pinyin but let Western names parse falsely.
Then drops a small casefold blocklist of tokens that still segment as pinyin but are
overwhelmingly non-Chinese in this pool (English, Hispanic, Arabic, etc.).

Surnames and tier_probs are unchanged. Re-tiers given names 20 / 30 / 50 / rest.

Run: python scripts/cleanse_chn_nonchinese_givens.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_POOL = _REPO / "data" / "name_pools" / "country_CHN.json"
_SYLLABLES_FILE = _REPO / "data" / "chinese_pinyin_syllables.txt"

# Tokens that segment as pinyin but are not treated as Chinese given names here.
_NON_CHINESE_GIVEN_CF: frozenset[str] = frozenset(
    {
        "dean",
        "duncan",
        "gene",
        "hadi",
        "hakan",
        "hasan",
        "julian",
        "juan",
        "ken",
        "lance",
        "lee",
        "leo",
        "luke",
        "mario",
        "mike",
        "neo",
        "owen",
        "sami",
        "sean",
        "shane",
        "terence",
        "zeeshan",
    }
)

# Syllables removed from the table: lone a/m/n let Alan, Jim, Simon, etc. parse.
_SYLLABLE_EXCLUDE = frozenset({"a", "m", "n"})


def _load_syllables() -> frozenset[str]:
    raw = _SYLLABLES_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(s.strip().casefold() for s in raw if s.strip() and s.strip().casefold() not in _SYLLABLE_EXCLUDE)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip())
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _is_pinyin_only(low: str, syl: frozenset[str], max_len: int) -> bool:
    """Segment whole token into 1–4 Mandarin syllables (backtracking; greedy fails e.g. jianguo)."""
    low = low.casefold()
    if not low or not re.fullmatch(r"[a-z]+", low):
        return False
    if low in _NON_CHINESE_GIVEN_CF:
        return False
    n = len(low)

    def segment(pos: int, used: int) -> bool:
        if pos == n:
            return 1 <= used <= 4
        if used >= 4:
            return False
        for L in range(min(max_len, n - pos), 0, -1):
            if low[pos : pos + L] in syl and segment(pos + L, used + 1):
                return True
        return False

    return segment(0, 0)


def _tier_20_30_50(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def main() -> None:
    syl = _load_syllables()
    max_len = max(len(x) for x in syl)

    data = json.loads(_POOL.read_text(encoding="utf-8"))
    g = data.get("given_names_male")
    if not isinstance(g, dict):
        raise SystemExit("given_names_male missing")
    flat: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        arr = g.get(tier)
        if isinstance(arr, list):
            flat.extend(_norm(x) for x in arr if isinstance(x, str) and _norm(x))

    seen: set[str] = set()
    kept: list[str] = []
    removed: list[str] = []
    for n in flat:
        cf = n.casefold()
        if cf in seen:
            continue
        if _is_pinyin_only(cf, syl, max_len):
            seen.add(cf)
            kept.append(n)
        else:
            removed.append(n)

    data["given_names_male"] = _tier_20_30_50(kept)
    _POOL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"kept {len(kept)} given names, removed {len(removed)} (deduped order preserved)")
    print("removed sample:", sorted({x.casefold() for x in removed})[:50], "...")


if __name__ == "__main__":
    main()
