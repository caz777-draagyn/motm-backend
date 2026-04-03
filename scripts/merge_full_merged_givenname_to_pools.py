#!/usr/bin/env python3
"""
Read repo root fullMergedGivenname (tab-separated: country, name, rank).

1. Map CSV country labels to pool country_name (see CSV_TO_POOL_NAME).
2. Merge rows that share the same target pool (e.g. duplicate CSV labels mapping to one pool).
3. Dedupe names per country (NFC trim, casefold), preserve first-seen order.
4. Re-rank 1..n per country; replace given_names_male: 20 / 30 / 50 / rest.
5. Strip country / city geo tokens via remove_country_tokens_from_pools (same ban + allow).

Run from repo root: python scripts/merge_full_merged_givenname_to_pools.py
"""

from __future__ import annotations

import csv
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from remove_country_tokens_from_pools import _build_ban_set, scrub_geo_tokens_in_name_block

_REPO = Path(__file__).resolve().parent.parent
CSV_PATH = _REPO / "fullMergedGivenname"
POOL_DIR = _REPO / "data" / "name_pools"

# CSV label -> pool JSON country_name (must match exactly one pool)
CSV_TO_POOL_NAME: dict[str, str] = {
    "Macedonia": "North Macedonia",
    # CSV "Congo" = DR Congo (Kinshasa); "Republic of the Congo" is Brazzaville (separate pool)
    "Congo": "DR Congo",
    # Alternate CSV label
    "Republic of Congo": "Republic of the Congo",
    # Source file mislabels South African names as Mayotte
    "Mayotte": "South Africa",
}

# No country_*.json pool for these; rows are skipped (see stderr summary)
SKIP_CSV_COUNTRIES: frozenset[str] = frozenset(
    {
        "United Kingdom",
    }
)


def _discover_pools() -> dict[str, Path]:
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


def _pool_for_label(csv_country: str, pools: dict[str, Path]) -> str:
    if csv_country in SKIP_CSV_COUNTRIES:
        raise KeyError("_skip")
    target = CSV_TO_POOL_NAME.get(csv_country, csv_country)
    if target not in pools:
        raise KeyError(target)
    return target


def _tier_lists(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"Missing {CSV_PATH}")

    pools = _discover_pools()
    ban = _build_ban_set()

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        if not r.fieldnames or set(r.fieldnames) != {"country", "name", "rank"}:
            raise SystemExit(f"Expected columns country, name, rank; got {r.fieldnames}")
        rows = list(r)

    for row in rows:
        row["_country"] = (row.get("country") or "").strip()
        row["_name"] = (row.get("name") or "").strip()
        try:
            row["_rank"] = int((row.get("rank") or "").strip())
        except ValueError:
            raise SystemExit(f"Bad rank for row {row!r}") from None

    # pool_country -> list of (source_csv_country, rank, name)
    by_pool: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    skipped_rows = 0
    unmapped: dict[str, int] = defaultdict(int)

    for row in rows:
        c = row["_country"]
        n = row["_name"]
        if not c or not n:
            continue
        try:
            pc = _pool_for_label(c, pools)
        except KeyError as e:
            if str(e) == "'_skip'":
                skipped_rows += 1
                continue
            unmapped[c] += 1
            continue
        by_pool[pc].append((c, row["_rank"], n))

    if unmapped:
        print("CSV countries with no matching pool (rows skipped):", file=sys.stderr)
        for k in sorted(unmapped.keys(), key=str.casefold):
            print(f"  {k!r}: {unmapped[k]} rows", file=sys.stderr)
        raise SystemExit(1)

    if skipped_rows:
        print(
            f"Skipped {skipped_rows} rows (no pool for {sorted(SKIP_CSV_COUNTRIES)}).",
            file=sys.stderr,
        )

    updated = 0
    scrub_total = 0
    for pool_country in sorted(by_pool.keys(), key=str.casefold):
        fp = pools[pool_country]
        bucket = by_pool[pool_country]
        bucket.sort(key=lambda t: (t[0].casefold(), t[1], t[2].casefold()))

        seen_cf: set[str] = set()
        names: list[str] = []
        for _src, _rank, raw in bucket:
            name = unicodedata.normalize("NFC", raw.strip())
            if not name:
                continue
            cf = name.casefold()
            if cf in seen_cf:
                continue
            seen_cf.add(cf)
            names.append(name)

        data = json.loads(fp.read_text(encoding="utf-8"))
        if "given_names_male" not in data:
            raise SystemExit(f"{fp.name} missing given_names_male")

        data["given_names_male"] = _tier_lists(names)
        removed = scrub_geo_tokens_in_name_block(data["given_names_male"], ban)
        scrub_total += len(removed)

        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {pool_country} ({fp.name}): {len(names)} names, geo scrub removed {len(removed)}")
        updated += 1

    print(f"Updated {updated} pool files; {scrub_total} given-name tokens removed by geo scrub.")


if __name__ == "__main__":
    main()
