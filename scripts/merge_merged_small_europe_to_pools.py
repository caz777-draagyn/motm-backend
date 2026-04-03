#!/usr/bin/env python3
"""
Read repo root mergedSmallEurope.csv (tab-separated: country, name, rank).

1. Sort by country (alphabetical), then rank, then name (stable).
2. Renumber rank per country to 1..n; overwrite mergedSmallEurope.csv.
3. For each country, map to data/name_pools/country_*.json via country_name (see
   CSV_COUNTRY_ALIASES for CSV labels that differ from pool JSON).
4. Replace given_names_male entirely: 20 / 30 / 50 / rest tier split.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
CSV_PATH = _REPO / "mergedSmallEurope.csv"
POOL_DIR = _REPO / "data" / "name_pools"

# CSV "country" cell -> pool JSON country_name when they differ
CSV_COUNTRY_ALIASES: dict[str, str] = {
    "Macedonia": "North Macedonia",
}


def _discover_pools() -> dict[str, Path]:
    """canonical country_name -> json path"""
    out: dict[str, Path] = {}
    for fp in sorted(POOL_DIR.glob("country_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip {fp.name}: {e}", file=sys.stderr)
            continue
        name = (data.get("country_name") or "").strip()
        if name:
            out[name] = fp
    return out


def _pool_name_for_csv_country(csv_country: str, pools: dict[str, Path]) -> str:
    raw = (csv_country or "").strip()
    target = CSV_COUNTRY_ALIASES.get(raw, raw)
    cf = target.casefold()
    for canon in pools:
        if canon.casefold() == cf:
            return canon
    raise KeyError(f"No pool for CSV country {raw!r} (tried {target!r})")


def _tier_lists(names: list[str]) -> dict[str, list[str]]:
    vc = names[:20]
    co = names[20:50]
    mid = names[50:100]
    rare = names[100:]
    return {
        "very_common": vc,
        "common": co,
        "mid": mid,
        "rare": rare,
    }


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"Missing {CSV_PATH}")

    pools = _discover_pools()
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        if not r.fieldnames or set(r.fieldnames) != {"country", "name", "rank"}:
            raise SystemExit(f"Expected columns country, name, rank; got {r.fieldnames}")
        rows = list(r)

    for row in rows:
        row["country"] = (row.get("country") or "").strip()
        row["name"] = (row.get("name") or "").strip()
        try:
            row["_rank"] = int((row.get("rank") or "").strip())
        except ValueError:
            raise SystemExit(f"Bad rank for row {row!r}") from None

    rows.sort(key=lambda x: (x["country"].casefold(), x["_rank"], x["name"].casefold()))

    by_country: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_country[row["country"]].append(row)

    out_rows: list[dict[str, str]] = []
    for csv_c in sorted(by_country.keys(), key=str.casefold):
        bucket = by_country[csv_c]
        for i, row in enumerate(bucket, start=1):
            row["rank"] = str(i)
            out_rows.append(
                {
                    "country": row["country"],
                    "name": row["name"],
                    "rank": row["rank"],
                }
            )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["country", "name", "rank"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    print(f"Wrote sorted + re-ranked {CSV_PATH} ({len(out_rows)} rows)")

    updated = 0
    for csv_c in sorted(by_country.keys(), key=str.casefold):
        pool_name = _pool_name_for_csv_country(csv_c, pools)
        fp = pools[pool_name]
        names = [row["name"] for row in by_country[csv_c] if row["name"]]
        data = json.loads(fp.read_text(encoding="utf-8"))
        if "given_names_male" not in data:
            raise SystemExit(f"{fp.name} missing given_names_male")
        data["given_names_male"] = _tier_lists(names)
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {pool_name} ({fp.name}): {len(names)} names")
        updated += 1

    print(f"Updated {updated} pool files.")


if __name__ == "__main__":
    main()
