"""
Validate naming pools referenced in FullHeritageAndNamingComposition.txt and local_core JSON.

Run from repo root: python scripts/validate_composition_naming_pools.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import heritage_composition  # noqa: E402
from utils import name_data  # noqa: E402
from utils.name_data import _alias_local_core_pool_id  # noqa: E402


def _all_pool_ids_on_disk() -> Set[str]:
    d = ROOT / "data" / "name_pools"
    out: Set[str] = set()
    for pattern in ("country_*.json", "custom_*.json"):
        for fp in sorted(d.glob(pattern)):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            code = data.get("country_code")
            if not code:
                continue
            pid = data.get("pool_id") or f"country_{code}"
            out.add(pid)
    return out


def _load_local_core_frozen() -> Dict[str, Any]:
    p = ROOT / "data" / "heritage_composition" / "local_core_naming_pools.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def main() -> Tuple[int, int, int]:
    pool_map = heritage_composition._build_pool_name_to_code()
    label_to_pool_id = heritage_composition._build_label_to_pool_id()

    text = (ROOT / "data" / "heritage_composition" / "FullHeritageAndNamingComposition.txt").read_text(
        encoding="utf-8"
    )
    lines = text.splitlines()
    if len(lines) < 2:
        print("No composition rows.")
        return 0, 0, 1

    use_nat_code = heritage_composition.composition_has_nationality_code_column(lines[0])
    country_map = heritage_composition._build_country_display_to_code()

    unresolved_examples: Dict[str, List[str]] = {}
    total_rows = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if use_nat_code:
            if len(parts) < 7:
                continue
            naming_pool_s = parts[5]
        else:
            if len(parts) < 6:
                continue
            if len(parts) >= 7:
                naming_pool_s = parts[4]
            else:
                naming_pool_s = parts[4]

        _, unresolved = heritage_composition.parse_pool_weights_unresolved(
            naming_pool_s, pool_map, label_to_pool_id
        )
        if unresolved:
            unresolved_examples[naming_pool_s] = unresolved
        total_rows += 1

    disk_ids = _all_pool_ids_on_disk()
    loaded_ids = set(name_data.NAME_POOLS_BY_ID.keys())

    used_in_composition: Set[str] = set()
    rows = heritage_composition.load_composition_rows()
    for r in rows:
        ow = r.get("origin_pool_weights") or {}
        used_in_composition.update(ow.keys())

    local_core = _load_local_core_frozen()
    used_in_local: Set[str] = set()
    for _nat, entries in local_core.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            if isinstance(e, dict) and e.get("pool_id"):
                used_in_local.add(_alias_local_core_pool_id(str(e["pool_id"])))

    used_all = used_in_composition | used_in_local
    missing_in_loader = sorted(used_all - loaded_ids)
    missing_on_disk = sorted(used_all - disk_ids)

    print("=== Composition naming pool labels ===")
    print(f"Rows scanned (raw lines): {total_rows}, load_composition_rows: {len(rows)}")
    if unresolved_examples:
        print(f"\nFAILED: {len(unresolved_examples)} distinct naming-pool strings have unresolved labels:")
        for s, bad in sorted(unresolved_examples.items())[:40]:
            print(f"  {bad!r} in: {s[:100]}{'...' if len(s) > 100 else ''}")
        if len(unresolved_examples) > 40:
            print(f"  ... and {len(unresolved_examples) - 40} more")
    else:
        print("All weighted labels resolve to a pool_id (or country_<code> fallback).")

    print("\n=== Pool IDs referenced (composition origin_pool_weights union local_core JSON) ===")
    print(f"Unique pool_ids from composition: {len(used_in_composition)}")
    print(f"Unique pool_ids from local_core_naming_pools.json: {len(used_in_local)}")
    print(f"Union: {len(used_all)}")

    print("\n=== Existence in name_data.NAME_POOLS_BY_ID (after load + heritage overlay) ===")
    if missing_in_loader:
        print(f"MISSING in NAME_POOLS_BY_ID ({len(missing_in_loader)}):")
        for x in missing_in_loader[:50]:
            print(f"  {x}")
        if len(missing_in_loader) > 50:
            print(f"  ... and {len(missing_in_loader) - 50} more")
    else:
        print("All referenced pool_ids are loaded.")

    if missing_on_disk:
        print(f"\nNote: {len(missing_on_disk)} referenced ids not found as country_/custom_ JSON filenames (may be OK if only dynamic).")
        for x in missing_on_disk[:20]:
            print(f"  {x}")

    print("\n=== Pools on disk not referenced by composition or frozen local_core ===")
    orphans = sorted(disk_ids - used_all)
    print(f"Orphan count: {len(orphans)}")
    for x in orphans[:80]:
        print(f"  {x}")
    if len(orphans) > 80:
        print(f"  ... and {len(orphans) - 80} more")

    err = 1 if unresolved_examples or missing_in_loader else 0
    return len(unresolved_examples), len(missing_in_loader), err


if __name__ == "__main__":
    n1, n2, code = main()
    sys.exit(code)
