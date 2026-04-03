#!/usr/bin/env python3
"""
One-time / repeatable migration:
  - Rename data/name_pools/<CODE>.json -> country_<CODE>.json and add pool_id.
  - Write data/heritage_composition/local_core_naming_pools_generated.json (regenerated from the .txt).
    Note: `data/heritage_composition/local_core_naming_pools.json` is treated as frozen manual data
    and will only be created if it does not exist yet.
  - Write data/heritage_composition/heritage_groups_export.json (snapshot from composition).

Composition file: FullHeritageAndNamingComposition.txt — columns include Region, NationalityCode,
Country, VisualBucket, percent, naming pool, naming split (see utils/heritage_composition.py).

Run from repo root: python scripts/migrate_naming_and_heritage_exports.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from utils.heritage_composition import (  # noqa: E402
    build_heritage_groups_from_rows,
    build_local_core_naming_pools,
    load_composition_rows,
)


def migrate_name_pool_files() -> int:
    pools_dir = _REPO / "data" / "name_pools"
    n = 0
    for fp in sorted(pools_dir.glob("*.json")):
        name = fp.name
        if name.startswith("country_") or name.startswith("custom_"):
            continue
        m = re.match(r"^([A-Z]{3})\.json$", name)
        if not m:
            continue
        code = m.group(1)
        dest = pools_dir / f"country_{code}.json"
        if dest.is_file():
            fp.unlink()
            n += 1
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        if "pool_id" not in data:
            data["pool_id"] = f"country_{code}"
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        fp.unlink()
        n += 1
    return n


def main() -> None:
    rows = load_composition_rows()
    if not rows:
        print("No composition rows; check data/heritage_composition/FullHeritageAndNamingComposition.txt")
        return

    n_migrated = migrate_name_pool_files()
    print(f"Migrated / reconciled name pool files: {n_migrated}")

    local_core = build_local_core_naming_pools(rows)
    out_dir = _REPO / "data" / "heritage_composition"
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_path = out_dir / "local_core_naming_pools_generated.json"
    generated_path.write_text(
        json.dumps(local_core, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {generated_path} ({len(local_core)} nationalities)")

    frozen_path = out_dir / "local_core_naming_pools.json"
    if not frozen_path.is_file() or frozen_path.stat().st_size == 0:
        frozen_path.write_text(
            json.dumps(local_core, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Backfilled frozen {frozen_path}")

    heritage = build_heritage_groups_from_rows(rows)
    export_path = out_dir / "heritage_groups_export.json"
    export_path.write_text(
        json.dumps(heritage, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {export_path} ({len(heritage)} nationalities)")


if __name__ == "__main__":
    main()
