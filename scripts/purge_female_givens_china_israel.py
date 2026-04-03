#!/usr/bin/env python3
"""
Remove female given names mistakenly listed under given_names_male for
country_CHN and country_ISR. Surnames untouched. Re-tier 20 / 30 / 50 / rest.

Run: python scripts/purge_female_givens_china_israel.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
POOL_DIR = _REPO / "data" / "name_pools"

# Typical female (English / intl) — applied to CHN and ISR male pools.
GLOBAL_FEMALE_GIVEN_CF: frozenset[str] = frozenset(
    {
        "alexis",
        "jen",
        "joan",
        "nicola",
        "taylor",
    }
)

# Hebrew / Israeli female givens often mis-filed under male — ISR given_names only.
ISR_FEMALE_GIVEN_CF: frozenset[str] = frozenset(
    {
        "michal",
        "shir",
        "sivan",
        "ronit",
        "nofar",
        "rinat",
        "stav",
        "gali",
        "chen",  # Hebrew חן; distinct from Chinese 陈 as surname token in CHN
    }
)


def _nf(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _tier_20_30_50(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _flatten_givens(data: dict) -> list[str]:
    g = data.get("given_names_male")
    if not isinstance(g, dict):
        return []
    out: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        arr = g.get(tier)
        if isinstance(arr, list):
            out.extend(_nf(x) for x in arr if isinstance(x, str) and _nf(x))
    return out


def _purge_pool(path: Path, *, extra_female_cf: frozenset[str] | None = None) -> tuple[int, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    flat = _flatten_givens(data)
    ban = GLOBAL_FEMALE_GIVEN_CF | (extra_female_cf or frozenset())
    removed: list[str] = []
    seen: set[str] = set()
    kept: list[str] = []
    for n in flat:
        cf = n.casefold()
        if cf in ban:
            removed.append(n)
            continue
        if cf in seen:
            continue
        seen.add(cf)
        kept.append(n)
    data["given_names_male"] = _tier_20_30_50(kept)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(kept), removed


def main() -> None:
    chn = POOL_DIR / "country_CHN.json"
    isr = POOL_DIR / "country_ISR.json"
    n_c, r_c = _purge_pool(chn, extra_female_cf=None)
    n_i, r_i = _purge_pool(isr, extra_female_cf=ISR_FEMALE_GIVEN_CF)
    print(f"country_CHN.json: removed {len(r_c)} -> {n_c} given names")
    print(f"  {sorted(set(r_c), key=str.casefold)}")
    print(f"country_ISR.json: removed {len(r_i)} -> {n_i} given names")
    print(f"  {sorted(set(r_i), key=str.casefold)}")


if __name__ == "__main__":
    main()
