#!/usr/bin/env python3
"""Print markdown table: per pool, counts by tier for given_names_male vs surnames."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.name_data import NAME_POOL_TIER_KEYS  # noqa: E402

POOLS = ROOT / "data" / "name_pools"
TIERS = NAME_POOL_TIER_KEYS


def main() -> int:
    rows = []
    for pat in ("country_*.json", "custom_*.json"):
        for p in sorted(POOLS.glob(pat)):
            if "_backup" in str(p) or "old" in p.parts:
                continue
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            pid = d.get("pool_id") or p.stem
            cc = d.get("country_code") or ""
            g = d.get("given_names_male") or {}
            s = d.get("surnames") or {}

            def cnt(block: dict, t: str) -> int:
                v = block.get(t)
                return len(v) if isinstance(v, list) else 0

            row = {"pool_id": pid, "code": cc}
            for t in TIERS:
                row[f"G_{t}"] = cnt(g, t)
            for t in TIERS:
                row[f"S_{t}"] = cnt(s, t)
            row["G_tot"] = sum(row[f"G_{t}"] for t in TIERS)
            row["S_tot"] = sum(row[f"S_{t}"] for t in TIERS)
            rows.append(row)

    agg = {f"G_{t}": 0 for t in TIERS} | {f"S_{t}": 0 for t in TIERS}
    for r in rows:
        for t in TIERS:
            agg[f"G_{t}"] += r[f"G_{t}"]
            agg[f"S_{t}"] += r[f"S_{t}"]

    gtot = sum(agg[f"G_{t}"] for t in TIERS)
    stot = sum(agg[f"S_{t}"] for t in TIERS)

    def tier_cells(prefix: str) -> str:
        return " | ".join(str(agg[f"{prefix}_{t}"]) for t in TIERS)

    hdr = (
        "| pool_id | code | "
        + " | ".join(f"G_{t}" for t in TIERS)
        + " | G_tot | "
        + " | ".join(f"S_{t}" for t in TIERS)
        + " | S_tot |"
    )
    ncols = 2 + len(TIERS) + 1 + len(TIERS) + 1
    sep = "|" + "|".join(["---"] * ncols) + "|"
    lines = [hdr, sep]
    lines.append(
        f"| **ALL ({len(rows)} pools)** | | {tier_cells('G')} | {gtot} | {tier_cells('S')} | {stot} |"
    )
    for r in rows:
        gcells = " | ".join(str(r[f"G_{t}"]) for t in TIERS)
        scells = " | ".join(str(r[f"S_{t}"]) for t in TIERS)
        lines.append(f"| {r['pool_id']} | {r['code']} | {gcells} | {r['G_tot']} | {scells} | {r['S_tot']} |")
    text = "\n".join(lines) + "\n"

    out_dir = ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "name_pool_tier_counts.md"
    out_path.write_text(text, encoding="utf-8")
    print(text, end="")
    print(f"\nWrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
