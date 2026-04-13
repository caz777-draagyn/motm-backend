#!/usr/bin/env python3
"""
Write per-pool ``tier_probs`` from rarity profiles and name counts.

Reads ``data/name_pools/masterInput/Pool_rarity_profiles.csv`` (override with --profiles-csv).

**Default data layout (tab or comma, no header):** three columns in order
``pool``, ``surname`` profile, ``given`` profile — e.g. ``country_FRA<TAB>BROAD<TAB>MEDIUM``.

**With a header row:** ``DictReader`` is used; columns may be named ``pool`` / ``pool_id``,
``surname`` / ``surname_profile``, ``given`` / ``given_profile`` (given/surname order in the
file does not matter when headers name the columns).

Profiles: CONCENTRATED, MEDIUM, BROAD, TINY, SPECIAL (SPECIAL = keep existing JSON branch).

Missing pools default to MEDIUM for both branches. Run from repo root:
  python scripts/apply_pool_tier_probs.py
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.name_data import NAME_POOL_TIER_KEYS
from utils.tier_prob_profiles import compute_tier_probs, count_branch_names, normalize_profile_token

NAME_POOLS_DIR = ROOT / "data" / "name_pools"
DEFAULT_CSV = NAME_POOLS_DIR / "masterInput" / "Pool_rarity_profiles.csv"


def _norm_header(k: str) -> str:
    return (k or "").strip().lower().lstrip("\ufeff")


def _looks_like_header_row(cells: list[str]) -> bool:
    if not cells:
        return False
    h0 = _norm_header(cells[0])
    if h0 in ("pool", "pool_id", "naming_pool"):
        return True
    joined = " ".join(_norm_header(c) for c in cells)
    return "given_profile" in joined or "surname_profile" in joined


def load_profiles(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return out
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return out
    first_line = text.splitlines()[0]
    delim = "\t" if "\t" in first_line else ","
    buf = io.StringIO(text)
    reader = csv.reader(buf, delimiter=delim)
    rows = [[(c or "").strip() for c in row] for row in reader if any((c or "").strip() for c in row)]
    if not rows:
        return out

    if _looks_like_header_row(rows[0]):
        buf2 = io.StringIO(text)
        dr = csv.DictReader(buf2, delimiter=delim)
        for raw in dr:
            row = {_norm_header(k): (v or "").strip() for k, v in raw.items()}
            pid = row.get("pool_id") or row.get("pool") or ""
            if not pid:
                continue
            g = row.get("given_profile") or row.get("given") or "MEDIUM"
            s = row.get("surname_profile") or row.get("surname") or "MEDIUM"
            out[pid] = {"given": g or "MEDIUM", "surname": s or "MEDIUM"}
        return out

    # No header: pool, surname, given
    for parts in rows:
        if len(parts) < 3:
            continue
        pid = parts[0].strip()
        if not pid or pid.startswith("#"):
            continue
        s_prof = parts[1].strip() or "MEDIUM"
        g_prof = parts[2].strip() or "MEDIUM"
        out[pid] = {"given": g_prof, "surname": s_prof}
    return out


def _normalize_branch_probs(d: object) -> dict[str, float]:
    if not isinstance(d, dict):
        return {k: 1.0 / len(NAME_POOL_TIER_KEYS) for k in NAME_POOL_TIER_KEYS}
    s = sum(max(0.0, float(d.get(k, 0) or 0)) for k in NAME_POOL_TIER_KEYS)
    if s <= 1e-15:
        return {k: 1.0 / len(NAME_POOL_TIER_KEYS) for k in NAME_POOL_TIER_KEYS}
    return {k: max(0.0, float(d.get(k, 0) or 0)) / s for k in NAME_POOL_TIER_KEYS}


def branch_probs_for_write(
    branch: str,
    profile_raw: str,
    n_total: int,
    existing_full: dict,
) -> dict[str, float]:
    prof = normalize_profile_token(profile_raw)
    if prof == "SPECIAL":
        old = existing_full.get(branch) if isinstance(existing_full, dict) else None
        return _normalize_branch_probs(old)
    return compute_tier_probs(branch, prof, n_total)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profiles-csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--pools-dir", type=Path, default=NAME_POOLS_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    profiles = load_profiles(args.profiles_csv)
    pools_root = args.pools_dir.resolve()

    touched = 0
    for pattern in ("country_*.json", "custom_*.json"):
        for path in sorted(pools_root.glob(pattern)):
            if path.parent.resolve() != pools_root:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Skip {path.name}: {e}", file=sys.stderr)
                continue
            pool_id = (data.get("pool_id") or path.stem).strip()
            if not pool_id.startswith("country_") and not pool_id.startswith("custom_"):
                continue
            if "given_names_male" not in data or "surnames" not in data:
                continue

            row = profiles.get(pool_id, {})
            g_prof = row.get("given", "MEDIUM") or "MEDIUM"
            s_prof = row.get("surname", "MEDIUM") or "MEDIUM"

            old_tp = data.get("tier_probs") if isinstance(data.get("tier_probs"), dict) else {}
            ng = count_branch_names(data.get("given_names_male"))
            ns = count_branch_names(data.get("surnames"))

            new_tp = {
                "given": branch_probs_for_write("given", g_prof, ng, old_tp),
                "surname": branch_probs_for_write("surname", s_prof, ns, old_tp),
            }
            data["tier_probs"] = new_tp
            if args.dry_run:
                print(f"{pool_id}: would set tier_probs (given_n={ng} surname_n={ns})")
                touched += 1
                continue

            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            touched += 1

    print(f"Done. Pools updated: {touched} dry_run={args.dry_run}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
