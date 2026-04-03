#!/usr/bin/env python3
"""
Move custom_* name pools that represent a whole nation (exact country name) into country_<CODE>.json.

Sub-national, linguistic, regional, and cultural distinctions stay as custom_* (see KEEP_CUSTOM_LABELS).

Run from repo root: python scripts/migrate_custom_pools_to_country_files.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_POOLS = _REPO / "data" / "name_pools"


def _norm(s: str) -> str:
    return s.strip().lower()


# Labels that must remain custom_* (not merged into a single country_<CODE> file).
KEEP_CUSTOM_LABELS = frozenset(
    _norm(x)
    for x in [
        "Belgium Dutch",
        "Belgium French",
        "China North",
        "China South",
        "Pakistan Punjabi",
        "Pakistan Pashtun",
        "Pakistan Sindhi",
        "India Punjabi",
        "India Gangetic",
        "India Bengali",
        "Tamil",
        "Telugu",
        "Kannada",
        "Malayalam",
        "Malaylam",
        "Malaysia Chinese",
        "Malaysia Indian",
        "Malaysia Malay",
        "Indonesia Javanese",
        "Indonesia Sumatran",
        "Indonesia Other",
        "Israel Hebrew",
        "Afghanistan Dari",
        "Swiss German",
        "Swiss French",
        "Swiss Italian",
        "Singapore Chinese",
        "Singapore Indian",
        "Singapore Malay",
        "Catalan",
        "Catalanl",
        "Pays Basque",
        "French Caribbean",
        "Dutch Caribbean",
        "Suriname Hindustani",
        "Fiji Indian",
        "Fiji Indigenous",
        "Philippines Tagalog",
        "Philippines Visayan",
        "Polynesia",
        "New Zealand Māori",
        "German",
        "Gibraltar",
        "Sri Lanka Sinhala",
        "Melanesia",
        "Puerto Rico",
        "UAE",
        "Congo",
    ]
)


def main() -> None:
    migrated = 0
    removed_duplicate = 0
    skipped = 0

    for fp in sorted(_POOLS.glob("custom_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip {fp.name}: {e}")
            continue

        name = data.get("country_name")
        code = data.get("country_code")
        pid = data.get("pool_id") or ""
        if not name or not code or len(str(code)) != 3:
            skipped += 1
            continue
        code = str(code).upper()

        if _norm(name) in KEEP_CUSTOM_LABELS:
            skipped += 1
            continue

        if not str(pid).startswith("custom_"):
            skipped += 1
            continue

        dest = _POOLS / f"country_{code}.json"
        if dest.is_file():
            try:
                existing = json.loads(dest.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}
            ex_name = existing.get("country_name")
            if ex_name and _norm(ex_name) == _norm(name):
                fp.unlink()
                removed_duplicate += 1
                print(f"Removed duplicate custom (country file exists): {fp.name}")
            else:
                print(
                    f"Skip {fp.name}: country_{code}.json exists with different country_name "
                    f"({ex_name!r} vs {name!r})"
                )
                skipped += 1
            continue

        out = dict(data)
        out["pool_id"] = f"country_{code}"
        out["country_code"] = code
        out["country_name"] = name
        dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        fp.unlink()
        migrated += 1
        print(f"Migrated {fp.name} -> {dest.name}")

    print(
        f"Done: migrated={migrated}, removed_duplicate={removed_duplicate}, skipped_keep_or_other={skipped}"
    )


if __name__ == "__main__":
    main()
