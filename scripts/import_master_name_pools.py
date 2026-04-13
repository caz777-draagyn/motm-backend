#!/usr/bin/env python3
"""
Merge masterInput CSVs into data/name_pools/country_*.json and custom_*.json.

Sources (repo-relative):
  data/name_pools/masterInput/Final_mergedGivenNames.csv — comma; columns
    naming_pool,name_type,name,score,pool_seq
  data/name_pools/masterInput/Final_mergedSurNames.csv — tab; columns
    naming_pool,name_type,name,pool_seq

Tier assignment uses **file order**: 1-based row index within each naming_pool (given/surname
rows only), **not** the pool_seq column. Bands match utils.name_data.tier_key_for_pool_seq:
  top 1–5, very_common 6–15, common 16–39, familiar 40–75, uncommon 76–250,
  rare 251–1000, very_rare 1001+.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NAME_POOLS_DIR = ROOT / "data" / "name_pools"
MASTER_DIR = NAME_POOLS_DIR / "masterInput"
GIVEN_CSV = MASTER_DIR / "Final_mergedGivenNames.csv"
SURNAME_CSV = MASTER_DIR / "Final_mergedSurNames.csv"

from utils.name_data import NAME_POOL_TIER_KEYS, tier_key_for_pool_seq  # noqa: E402


def _uniform_tier_probs() -> Dict[str, Dict[str, float]]:
    u = 1.0 / len(NAME_POOL_TIER_KEYS)
    d = {k: u for k in NAME_POOL_TIER_KEYS}
    return {"given": dict(d), "surname": dict(d)}


def _empty_tiers() -> Dict[str, List[str]]:
    return {k: [] for k in NAME_POOL_TIER_KEYS}


def assign_names_to_tiers(rows: List[Tuple[str, int]]) -> Dict[str, List[str]]:
    """``rows`` are (name, file_order_1based) per pool; sort by file order; dedupe by casefold.

    Tier comes from file line index within the pool, not from pool_seq in the CSV.
    """
    rows_sorted = sorted(rows, key=lambda x: (x[1], x[0].casefold()))
    out = _empty_tiers()
    seen_cf: Set[str] = set()
    for name, line_rank in rows_sorted:
        n = (name or "").strip()
        if not n:
            continue
        cf = n.casefold()
        if cf in seen_cf:
            continue
        seen_cf.add(cf)
        try:
            r = int(line_rank)
        except (TypeError, ValueError):
            r = 0
        out[tier_key_for_pool_seq(r)].append(n)
    return out


def _norm_header_key(k: str) -> str:
    return (k or "").strip().removeprefix("\ufeff").strip().lower()


def _cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return _cell(v[0]) if v else ""
    return str(v).strip()


def read_given_rows(path: Path) -> DefaultDict[str, List[Tuple[str, int]]]:
    """Append (name, file_order_1based) per pool; order is CSV row order for given rows."""
    by_pool: DefaultDict[str, List[Tuple[str, int]]] = defaultdict(list)
    pool_line: DefaultDict[str, int] = defaultdict(int)
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            return by_pool
        for raw in r:
            row = {_norm_header_key(k): _cell(v) for k, v in raw.items()}
            if (row.get("name_type") or "").lower() != "given":
                continue
            pool = row.get("naming_pool") or ""
            name = row.get("name") or ""
            if not pool or not name:
                continue
            pool_line[pool] += 1
            by_pool[pool].append((name, pool_line[pool]))
    return by_pool


def read_surname_rows(path: Path) -> DefaultDict[str, List[Tuple[str, int]]]:
    """Append (name, file_order_1based) per pool; order is CSV row order for surname rows."""
    by_pool: DefaultDict[str, List[Tuple[str, int]]] = defaultdict(list)
    pool_line: DefaultDict[str, int] = defaultdict(int)
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f, delimiter="\t")
        if not r.fieldnames:
            return by_pool
        for raw in r:
            row = {_norm_header_key(k): _cell(v) for k, v in raw.items()}
            nt = (row.get("name_type") or "").lower()
            if nt not in ("last", "surname"):
                continue
            pool = row.get("naming_pool") or ""
            name = row.get("name") or ""
            if not pool or not name:
                continue
            pool_line[pool] += 1
            by_pool[pool].append((name, pool_line[pool]))
    return by_pool


def infer_country_code(pool_id: str) -> str:
    if pool_id.startswith("country_") and len(pool_id) > len("country_"):
        return pool_id[len("country_") :]
    return ""


# Master CSV may introduce custom_* pools with no prior JSON; loader requires country_code.
_CUSTOM_POOL_DEFAULT_CC = {
    "custom_philippines": "PHI",
    "custom_swiss": "SUI",
}


def should_skip_pool_path(p: Path) -> bool:
    if "_backup" in p.name:
        return True
    parts = {x.casefold() for x in p.parts}
    return "old" in parts


def surname_inherit_only(data: dict) -> bool:
    return bool((data.get("surname_inherit_pool_id") or "").strip()) and "surnames" not in data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print summary only; do not write JSON")
    ap.add_argument("--given-csv", type=Path, default=GIVEN_CSV)
    ap.add_argument("--surname-csv", type=Path, default=SURNAME_CSV)
    ap.add_argument("--pools-dir", type=Path, default=NAME_POOLS_DIR)
    args = ap.parse_args()

    if not args.given_csv.is_file():
        print(f"Missing given CSV: {args.given_csv}", file=sys.stderr)
        return 1
    if not args.surname_csv.is_file():
        print(f"Missing surname CSV: {args.surname_csv}", file=sys.stderr)
        return 1

    given_by_pool = read_given_rows(args.given_csv)
    sur_by_pool = read_surname_rows(args.surname_csv)
    all_pools = sorted(set(given_by_pool) | set(sur_by_pool))

    written = 0
    skipped_surname_inherit = 0
    for pool_id in all_pools:
        if not (pool_id.startswith("country_") or pool_id.startswith("custom_")):
            print(f"Skip unknown pool id shape: {pool_id!r}", file=sys.stderr)
            continue
        path = args.pools_dir / f"{pool_id}.json"
        existing: Dict[str, Any] = {}
        if path.is_file() and not should_skip_pool_path(path):
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: could not read {path}: {e}", file=sys.stderr)
                existing = {}

        inherit_only = surname_inherit_only(existing)
        has_g = pool_id in given_by_pool
        has_s = pool_id in sur_by_pool

        out = dict(existing)
        out["pool_id"] = pool_id
        cc = (out.get("country_code") or "").strip()
        if not cc:
            cc = infer_country_code(pool_id) or _CUSTOM_POOL_DEFAULT_CC.get(pool_id, "")
        if not cc:
            cc = "UNK"
        out["country_code"] = cc
        if has_g:
            out["given_names_male"] = assign_names_to_tiers(given_by_pool[pool_id])
        if has_s and not inherit_only:
            out["surnames"] = assign_names_to_tiers(sur_by_pool[pool_id])
        elif has_s and inherit_only:
            skipped_surname_inherit += 1

        if "tier_probs" not in out:
            out["tier_probs"] = _uniform_tier_probs()
        if "rarity_profile" not in out:
            out["rarity_profile"] = "mixed"

        g_n = sum(len(out.get("given_names_male", {}).get(t, []) or []) for t in NAME_POOL_TIER_KEYS) if isinstance(
            out.get("given_names_male"), dict
        ) else 0
        s_n = sum(len(out.get("surnames", {}).get(t, []) or []) for t in NAME_POOL_TIER_KEYS) if isinstance(
            out.get("surnames"), dict
        ) else 0

        if args.dry_run:
            print(f"{pool_id}: would write path={path.name} given_total={g_n} surname_total={s_n} new_file={not path.is_file()}")
            written += 1
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        written += 1

    print(
        f"Done. Pools touched: {written} (dry_run={args.dry_run}). "
        f"Skipped surname CSV merge (inherit-only layout): {skipped_surname_inherit}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
