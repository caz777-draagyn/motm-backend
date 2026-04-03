#!/usr/bin/env python3
"""
Read repo root mergedSurnameSmallEurope.csv and merge surnames into name pools.

Supported formats (tab-separated):
  A) Country name / Country Rank / NameLatin  (current export)
  B) country / name / rank  (legacy)

Rows with empty country or surname, or surname shorter than 2 characters, are skipped.
Within each country, rows are sorted by Country Rank, then NameLatin; ranks are
renumbered 1..n. Duplicate surnames (case-insensitive) keep the first occurrence.

Surname tiers (overwrite pool surnames only): 40 very_common, 60 common, 100 mid, rest rare.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
CSV_PATH = _REPO / "mergedSurnameSmallEurope.csv"
POOL_DIR = _REPO / "data" / "name_pools"

CSV_COUNTRY_ALIASES: dict[str, str] = {
    "Macedonia": "North Macedonia",
}

MIN_SURNAME_LEN = 2


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


def _pool_name_for_csv_country(csv_country: str, pools: dict[str, Path]) -> str:
    raw = (csv_country or "").strip()
    target = CSV_COUNTRY_ALIASES.get(raw, raw)
    cf = target.casefold()
    for canon in pools:
        if canon.casefold() == cf:
            return canon
    raise KeyError(f"No pool for CSV country {raw!r} (tried {target!r})")


def _tier_lists(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:40],
        "common": names[40:100],
        "mid": names[100:200],
        "rare": names[200:],
    }


def _parse_row(row: dict[str, str]) -> tuple[str, str, int] | None:
    if "Country name" in row and "NameLatin" in row:
        c = (row.get("Country name") or "").strip()
        n = (row.get("NameLatin") or "").strip()
        rk = row.get("Country Rank", "")
    elif "country" in row and "name" in row:
        c = (row.get("country") or "").strip()
        n = (row.get("name") or "").strip()
        rk = row.get("rank", "")
    else:
        return None
    if not c or not n or len(n) < MIN_SURNAME_LEN:
        return None
    try:
        ir = int(str(rk).strip())
    except ValueError:
        return None
    return (c, n, ir)


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"Missing {CSV_PATH}")

    pools = _discover_pools()
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        if not r.fieldnames:
            raise SystemExit("CSV has no header")
        raw_rows = list(r)

    parsed: list[tuple[str, str, int]] = []
    for row in raw_rows:
        t = _parse_row(row)
        if t:
            parsed.append(t)

    by_country: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for c, n, rk in parsed:
        by_country[c].append((n, rk))

    out_file_rows: list[dict[str, str]] = []
    pool_updates: dict[str, list[str]] = {}

    for csv_c in sorted(by_country.keys(), key=str.casefold):
        bucket = by_country[csv_c]
        bucket.sort(key=lambda x: (x[1], x[0].casefold()))
        seen: set[str] = set()
        names: list[str] = []
        for name, _rk in bucket:
            k = name.casefold()
            if k in seen:
                continue
            seen.add(k)
            names.append(name)

        for i, name in enumerate(names, start=1):
            out_file_rows.append(
                {
                    "Country name": csv_c,
                    "Country Rank": str(i),
                    "NameLatin": name,
                }
            )

        try:
            pool_name = _pool_name_for_csv_country(csv_c, pools)
        except KeyError:
            print(f"Skip pool update (no JSON): {csv_c!r} ({len(names)} surnames)", file=sys.stderr)
            continue
        pool_updates[pool_name] = names

    out_headers = ["Country name", "Country Rank", "NameLatin"]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_headers, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out_file_rows)

    print(f"Wrote sorted + deduped + re-ranked {CSV_PATH} ({len(out_file_rows)} rows)")

    updated = 0
    for pool_name, names in sorted(pool_updates.items(), key=lambda x: x[0].casefold()):
        fp = pools[pool_name]
        data = json.loads(fp.read_text(encoding="utf-8"))
        if "surnames" not in data or not isinstance(data["surnames"], dict):
            raise SystemExit(f"{fp.name} missing surnames object")
        data["surnames"] = _tier_lists(names)
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {pool_name} ({fp.name}): {len(names)} surnames")
        updated += 1

    print(f"Updated {updated} pool files (surnames only).")


if __name__ == "__main__":
    main()
