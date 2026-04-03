#!/usr/bin/env python3
"""
Create empty custom_*.json name pools for every composition naming label that is not
already represented by a country_<CODE>.json whose country_name matches the label.

Also writes data/name_pools/composition_pool_registry.json (coverage index).

Run from repo root:
  python scripts/generate_composition_custom_pools.py
  python scripts/generate_composition_custom_pools.py --registry-only   # refresh registry only; no pool file writes
  python scripts/generate_composition_custom_pools.py --prune-orphans --dry-run   # list custom_*.json no longer in composition
  python scripts/generate_composition_custom_pools.py --prune-orphans --registry-only   # delete orphans + refresh registry
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from utils import heritage_composition as hc  # noqa: E402

_COMPOSITION = _REPO / "data" / "heritage_composition" / "FullHeritageAndNamingComposition.txt"
_POOLS = _REPO / "data" / "name_pools"
_UNK = "UNK"


def _norm(s: str) -> str:
    return s.strip().lower()


def _slug(label: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", label.strip().lower())
    s = s.strip("_")
    return s or "pool"


def _empty_tiers() -> dict:
    return {
        "very_common": [],
        "common": [],
        "mid": [],
        "rare": [],
    }


def _collect_composition_labels() -> set[str]:
    text = _COMPOSITION.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        return set()
    # naming pool column: index 5 when NationalityCode is present, else 4 (legacy)
    naming_col = 5 if hc.composition_has_nationality_code_column(lines[0]) else 4
    out: set[str] = set()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) <= naming_col:
            continue
        s = parts[naming_col]
        for part in s.split(","):
            part = part.strip()
            if not part:
                continue
            m = re.match(r"^(.+?)\s+([\d.]+)\s*$", part)
            if m:
                out.add(m.group(1).strip())
    return out


def _canonical_country_names() -> set[str]:
    canon: set[str] = set()
    for fp in sorted(_POOLS.glob("country_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        name = data.get("country_name")
        if name:
            canon.add(_norm(name))
    return canon


def _prune_orphan_custom_pools(composition_labels: set[str], *, dry_run: bool) -> int:
    """
    Delete custom_*.json files whose country_name does not appear (case-insensitive) in any
    composition naming-pool label. Use after renaming/fixing typos in FullHeritageAndNamingComposition.txt.
    """
    ref = {_norm(x) for x in composition_labels}
    n = 0
    for fp in sorted(_POOLS.glob("custom_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        name = data.get("country_name")
        if not name:
            continue
        if _norm(name) in ref:
            continue
        if dry_run:
            print(f"Would remove orphan: {fp.name} (country_name={name!r})")
        else:
            fp.unlink()
            print(f"Removed orphan: {fp.name} (country_name={name!r})")
        n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description="Composition naming labels → custom pools + registry")
    ap.add_argument(
        "--registry-only",
        action="store_true",
        help="Only rewrite composition_pool_registry.json from the current composition file (no custom_*.json writes).",
    )
    ap.add_argument(
        "--prune-orphans",
        action="store_true",
        help="Remove custom_*.json whose country_name never appears in the composition naming-pool column.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="With --prune-orphans, only print what would be removed (no deletes).",
    )
    args = ap.parse_args()

    labels_set = _collect_composition_labels()
    if args.prune_orphans:
        n_pruned = _prune_orphan_custom_pools(labels_set, dry_run=args.dry_run)
        print(
            f"Orphan custom pools {'(dry-run) ' if args.dry_run else ''}"
            f"{'found' if args.dry_run else 'removed'}: {n_pruned}"
        )

    labels = sorted(labels_set)
    canon = _canonical_country_names()
    pool_map = hc._build_pool_name_to_code()

    registry = {
        "version": 1,
        "composition_file": str(_COMPOSITION.relative_to(_REPO)),
        "covered_by_country_name_match": [],
        "custom_pools": [],
    }

    slug_used: dict[str, str] = {}
    n_written = 0

    for label in labels:
        if _norm(label) in canon:
            registry["covered_by_country_name_match"].append(label)
            continue

        code = hc.pool_label_to_code(label, pool_map) or _UNK
        base = _slug(label)
        slug = base
        n = 2
        while slug in slug_used and slug_used[slug] != label:
            slug = f"{base}_{n}"
            n += 1
        slug_used[slug] = label

        pool_id = f"custom_{slug}"
        fname = f"{pool_id}.json"
        path = _POOLS / fname

        if not args.registry_only:
            payload = {
                "pool_id": pool_id,
                "country_code": code,
                "country_name": label,
                "given_names_male": _empty_tiers(),
                "surnames": _empty_tiers(),
            }

            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            n_written += 1
        registry["custom_pools"].append(
            {
                "composition_label": label,
                "pool_id": pool_id,
                "file": fname,
                "country_code": code,
            }
        )

    reg_path = _POOLS / "composition_pool_registry.json"
    reg_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Composition labels: {len(labels)}; "
        f"covered by country_name match: {len(registry['covered_by_country_name_match'])}; "
        f"custom files written: {n_written}; "
        f"registry: {reg_path.relative_to(_REPO)}"
    )


if __name__ == "__main__":
    main()
