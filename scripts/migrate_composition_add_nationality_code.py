#!/usr/bin/env python3
"""
One-time migration: add an explicit NationalityCode column to FullHeritageAndNamingComposition.txt.

Old (6 data columns after header):
  Region \\t Country \\t VisualBucket \\t percent \\t naming pool \\t naming split

New (7 data columns):
  Region \\t NationalityCode \\t Country \\t VisualBucket \\t percent \\t naming pool \\t naming split

NationalityCode is resolved from Country using the same map as load_composition_rows() (legacy path).

Run from repo root: python scripts/migrate_composition_add_nationality_code.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from utils import heritage_composition as hc  # noqa: E402

_COMPOSITION = _REPO / "data" / "heritage_composition" / "FullHeritageAndNamingComposition.txt"


def _norm(s: str) -> str:
    return s.strip().lower()


def main() -> None:
    text = _COMPOSITION.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        print("Empty composition file")
        return
    if hc.composition_has_nationality_code_column(lines[0]):
        print("Already migrated (header has NationalityCode). Nothing to do.")
        return

    country_map = hc._build_country_display_to_code()
    out_lines = [
        "Region\tNationalityCode\tCountry\tVisualBucket\tpercent\tnaming pool\tnaming split"
    ]
    missing: list[str] = []
    for line in lines[1:]:
        if not line.strip():
            out_lines.append(line)
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            out_lines.append(line)
            continue
        region, country_disp, vb, pct, naming, split = parts[:6]
        cc = country_map.get(_norm(country_disp))
        if not cc:
            missing.append(country_disp.strip())
            continue
        cc = cc.upper()
        out_lines.append(
            "\t".join([region, cc, country_disp, vb, pct, naming, split])
        )

    if missing:
        uniq = sorted(set(missing))
        print(f"ERROR: {len(missing)} row(s) could not resolve NationalityCode for Country:")
        for u in uniq:
            print(f"  - {u!r}")
        print("Add these to name pools (country_name/country_code) or country_ovr in heritage_composition.py")
        raise SystemExit(1)

    _COMPOSITION.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Wrote {_COMPOSITION} ({len(out_lines) - 1} data rows + header)")


if __name__ == "__main__":
    main()
