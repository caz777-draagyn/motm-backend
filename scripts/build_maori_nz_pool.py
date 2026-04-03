#!/usr/bin/env python3
"""
Populate custom_new_zealand_m_ori.json with male givens + surnames for Maori NZ.

Source: scripts/data/maori_nz_givens.txt, maori_nz_surnames.txt (Latin letters incl. macrons).
Tiering: 20 / 30 / 50 / rest (cap ~220 givens, ~96 surnames).

Run: python scripts/build_maori_nz_pool.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from name_pool_text import canon_name, is_plausible_token

REPO = Path(__file__).resolve().parent.parent
NP = REPO / "data" / "name_pools"
DATA = Path(__file__).resolve().parent / "data"

TIERS = ("very_common", "common", "mid", "rare")

DROP_CF: frozenset[str] = frozenset(
    {
        "junior", "cj", "mj", "jr", "sr", "mr", "ms", "dr", "ii", "iii", "iv",
        "dad", "baby", "king", "queen", "shop", "girl", "joan", "mae", "rose",
        "joy", "anne", "nicole", "claire", "marie", "kim",
    }
)


def dedupe_first(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in names:
        c = canon_name(raw)
        if not c or not is_plausible_token(c):
            continue
        cf = c.casefold()
        if cf in DROP_CF:
            continue
        if cf in seen:
            continue
        seen.add(cf)
        out.append(c)
    return out


def tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def main() -> None:
    g_raw = _load_lines(DATA / "maori_nz_givens.txt")
    s_raw = _load_lines(DATA / "maori_nz_surnames.txt")

    givens = dedupe_first(g_raw)[:220]
    surnames = dedupe_first(s_raw)[:96]

    doc = {
        "pool_id": "custom_new_zealand_m_ori",
        "country_code": "NZL",
        "country_name": "New Zealand Māori",
        "given_names_male": tier(givens),
        "surnames": tier(surnames),
        "tier_probs": {
            "given": {"very_common": 0.55, "common": 0.3, "mid": 0.13, "rare": 0.02},
            "surname": {"very_common": 0.45, "common": 0.35, "mid": 0.17, "rare": 0.03},
        },
        "middle_name_prob": 0.12,
        "compound_surname_prob": 0.06,
        "surname_connector": "-",
    }

    (NP / "custom_new_zealand_m_ori.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    def ng(d: dict) -> int:
        return sum(len(d["given_names_male"][t]) for t in TIERS)

    def ns(d: dict) -> int:
        return sum(len(d["surnames"][t]) for t in TIERS)

    print(f"custom_new_zealand_m_ori: givens={ng(doc)} surnames={ns(doc)}")


if __name__ == "__main__":
    main()
