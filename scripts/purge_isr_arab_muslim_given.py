#!/usr/bin/env python3
"""
Remove Arab / Muslim / Palestine-typical given names from country_ISR.json;
re-tier 20 / 30 / 50 / rest. Surnames unchanged.

Run: python scripts/purge_isr_arab_muslim_given.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
POOL = _REPO / "data" / "name_pools" / "country_ISR.json"

# Casefold: typical Arabic / Muslim male given names (and spellings) to drop from ISR.
# Excludes names that are also normal Hebrew/Israeli (e.g. amir, omer, ram, ari).
ARAB_MUSLIM_GIVEN_CF: frozenset[str] = frozenset(
    {
        "abdullah",
        "abu",
        "abo",
        "abed",
        "adnan",
        "ahmad",
        "ahmed",
        "ali",
        "ammar",
        "amjad",
        "ameer",
        "amin",
        "amr",
        "ayman",
        "fadi",
        "hamza",
        "hasan",
        "hassan",
        "hussein",
        "ibrahim",
        "karim",
        "khaled",
        "khalid",
        "khalil",
        "mahmoud",
        "mohammad",
        "mohammed",
        "mohamed",
        "mohamad",
        "muhammad",
        "mostafa",
        "mustafa",
        "omar",
        "osama",
        "salah",
        "samir",
        "shadi",
        "tarek",
        "tariq",
        "waseem",
        "wisam",
        "yousef",
        "youssef",
    }
)

# For position report: stereotypical Russian / ex-USSR given names still in pool (casefold keys).
RUSSIAN_GIVEN_CF: frozenset[str] = frozenset(
    {
        "boris",
        "ilya",
        "oleg",
        "vladimir",
        "dmitry",
        "dmitri",
        "sergey",
        "sergei",
        "pavel",
        "vadim",
        "vlad",
        "leonid",
        "konstantin",
        "anton",
        "vitaly",
        "vitali",
        "nikita",
        "kirill",
        "alexey",
        "alexei",
        "andrey",
        "andrei",
        "roman",
        "denis",
        "maxim",
        "stas",
        "stanislav",
        "igor",
        "anatoly",
        "anatoli",
        "grégory",
        "gregory",
        "viktor",
        "victor",
        "yuri",
        "yury",
        "mikhail",
        "ivan",
    }
)


def _nf(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _flatten_with_positions(
    block: dict,
) -> tuple[list[str], list[tuple[str, int, str]]]:
    """names in order; positions as (tier, index_in_tier, name)."""
    names: list[str] = []
    positions: list[tuple[str, int, str]] = []
    for tier in ("very_common", "common", "mid", "rare"):
        arr = block.get(tier)
        if not isinstance(arr, list):
            continue
        for i, x in enumerate(arr):
            if not isinstance(x, str):
                continue
            n = _nf(x)
            if not n:
                continue
            names.append(n)
            positions.append((tier, i, n))
    return names, positions


def _tier_20_30_50(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def main() -> None:
    data = json.loads(POOL.read_text(encoding="utf-8"))
    g = data.get("given_names_male")
    if not isinstance(g, dict):
        raise SystemExit("missing given_names_male")

    flat, positions = _flatten_with_positions(g)

    # Russian report (original positions before purge)
    print("Russian / ex-USSR-flavored given names (original tier + index, 0-based):\n")
    for tier, idx, name in positions:
        cf = name.casefold()
        if cf in RUSSIAN_GIVEN_CF:
            print(f"  {tier}[{idx}]: {name}")
    print()

    seen: set[str] = set()
    kept: list[str] = []
    removed: list[str] = []
    for n in flat:
        cf = n.casefold()
        if cf in ARAB_MUSLIM_GIVEN_CF:
            removed.append(n)
            continue
        if cf in seen:
            continue
        seen.add(cf)
        kept.append(n)

    data["given_names_male"] = _tier_20_30_50(kept)
    POOL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Removed {len(removed)} Arab/Muslim tokens (dedupe after order): {sorted(set(removed), key=str.casefold)}")
    print(f"Kept {len(kept)} given names -> {POOL.name}")


if __name__ == "__main__":
    main()
