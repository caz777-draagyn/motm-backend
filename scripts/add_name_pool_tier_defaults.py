#!/usr/bin/env python3
"""
One-off: add tier_probs + middle_name_prob + compound_surname_prob + surname_connector
to name pool JSON files that are missing them (same tier_probs as country_SUD.json).

Custom pools get culture-aware middle/compound/connector heuristics; country_* stubs
match the existing full country files (0.15 / 0.05 / "-").
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Same as data/name_pools/country_SUD.json and utils/name_data.DEFAULT_*
TIER_PROBS = {
    "given": {
        "very_common": 0.55,
        "common": 0.3,
        "mid": 0.13,
        "rare": 0.02,
    },
    "surname": {
        "very_common": 0.45,
        "common": 0.35,
        "mid": 0.17,
        "rare": 0.03,
    },
}


def custom_sampling_defaults(pool_id: str) -> tuple[float, float, str]:
    """middle_name_prob, compound_surname_prob, surname_connector."""
    pid = pool_id.lower()

    # Iberian / Latin American–style heritage pools (compound surnames common)
    if pool_id in (
        "custom_catalan",
        "custom_puerto_rico",
        "custom_dutch_caribbean",
        "custom_french_caribbean",
    ):
        return (0.12, 0.12, " ")

    # East Asian: given + single family name; middle / compound rare in this model
    if pool_id in ("custom_china_north", "custom_china_south"):
        return (0.05, 0.02, "-")

    # South / Southeast Asian (including Indo-Pak, Malay archipelago, Lanka)
    if any(
        x in pid
        for x in (
            "india_",
            "pakistan_",
            "sri_lanka",
            "singapore_",
            "malaysia_",
            "indonesia_",
            "philippines_",
            "myanmar",
            "tamil",
            "telugu",
            "kannada",
            "malaylam",
            "afghanistan",
            "suriname_hindustani",
        )
    ):
        return (0.08, 0.04, "-")

    # Middle East / Gulf / Hebrew
    if pool_id in ("custom_uae", "custom_israel_hebrew"):
        return (0.10, 0.05, "-")

    # Pacific / Māori / Melanesia / Polynesia
    if any(
        x in pid
        for x in (
            "polynesia",
            "melanesia",
            "fiji_",
            "new_zealand",
        )
    ):
        return (0.12, 0.06, "-")

    # Sub-Saharan African heritage
    if "congo" in pid:
        return (0.12, 0.05, "-")

    # Western Europe microstates / Belgium / Swiss / Gibraltar / Basque
    return (0.15, 0.05, "-")


def main() -> None:
    pools_dir = _REPO / "data" / "name_pools"
    updated = 0
    for fp in sorted(pools_dir.glob("*.json")):
        if fp.name == "composition_pool_registry.json":
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        if "tier_probs" in data:
            continue

        pool_id = data.get("pool_id") or ""
        if not pool_id:
            print(f"skip (no pool_id): {fp.name}")
            continue

        if pool_id.startswith("custom_"):
            mid, compound, conn = custom_sampling_defaults(pool_id)
        else:
            mid, compound, conn = (0.15, 0.05, "-")

        data["tier_probs"] = copy.deepcopy(TIER_PROBS)
        data["middle_name_prob"] = mid
        data["compound_surname_prob"] = compound
        data["surname_connector"] = conn

        fp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        updated += 1
        print(f"updated {fp.name}")

    print(f"done: {updated} files")


if __name__ == "__main__":
    main()
