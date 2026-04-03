#!/usr/bin/env python3
"""
Load final_FirstName/*.txt and overwrite given_names_male in mapped pools.

Tier split: 20 very_common, 30 common, 50 mid, rest rare.

Run: python scripts/merge_final_firstname_to_pools.py
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
SRC_DIR = _REPO / "final_FirstName"
POOL_DIR = _REPO / "data" / "name_pools"

# source file (under final_FirstName/) -> pool JSON filename
FILE_TO_POOL: tuple[tuple[str, str], ...] = (
    ("swissGerman.txt", "custom_swiss_german.json"),
    ("swissFrench.txt", "custom_swiss_french.json"),
    ("swissItalian.txt", "custom_swiss_italian.json"),
    ("Final_BelgiumDutch.txt", "custom_belgium_dutch.json"),
    ("Final_BelgiumFrench.txt", "custom_belgium_french.json"),
    ("final_catalan.txt", "custom_catalan.json"),
    ("final_Basque.txt", "custom_pays_basque.json"),
    ("Final_England.txt", "country_ENG.json"),
    ("final_scotland.txt", "country_SCO.json"),
    ("final_wales.txt", "country_WAL.json"),
    ("final_northIreland.txt", "country_NIR.json"),
)


def _nf(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _tier_20_30_50_rest(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _rank_key(header: str) -> bool:
    h = header.strip().casefold()
    if h == "rank":
        return True
    if "rank" in h and "country" not in h:
        return True
    if re.match(r"ran\s*k", h):
        return True
    return False


def _parse_ranked_tsv(path: Path) -> list[str]:
    """Country name \\t Name \\t rank OR Name \\t Rank \\t Country."""
    text = path.read_text(encoding="utf-8-sig")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    r = csv.reader(lines, delimiter="\t")
    rows = list(r)
    header = [x.strip() for x in rows[0]]
    # Detect layout
    if len(header) >= 3 and header[0].casefold() in ("name",) and _rank_key(header[1]):
        # Name, Rank, Country
        idx_name, idx_rank = 0, 1
        data_rows = rows[1:]
    elif len(header) >= 3 and _rank_key(header[-1]):
        idx_name, idx_rank = 1, 2
        data_rows = rows[1:]
    else:
        # Fallback: assume col1 name, col2 rank
        idx_name, idx_rank = 1, 2
        data_rows = rows[1:]

    parsed: list[tuple[int, str]] = []
    for row in data_rows:
        if len(row) <= max(idx_name, idx_rank):
            continue
        name = _nf(row[idx_name])
        if not name:
            continue
        rank_s = _nf(row[idx_rank])
        try:
            rk = int(rank_s)
        except ValueError:
            rk = 10**9
        parsed.append((rk, name))

    parsed.sort(key=lambda t: (t[0], t[1].casefold()))
    seen: set[str] = set()
    out: list[str] = []
    for _r, name in parsed:
        cf = name.casefold()
        if cf in seen:
            continue
        seen.add(cf)
        out.append(name)
    return out


def _parse_bucket_tsv(path: Path) -> list[str]:
    """bucket \\t name \\t rarity — preserve file order after header."""
    text = path.read_text(encoding="utf-8-sig")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    r = csv.reader(lines, delimiter="\t")
    rows = list(r)
    header = [x.strip().casefold() for x in rows[0]]
    try:
        i_name = header.index("name")
    except ValueError:
        i_name = 1
    seen: set[str] = set()
    out: list[str] = []
    for row in rows[1:]:
        if len(row) <= i_name:
            continue
        name = _nf(row[i_name])
        if not name:
            continue
        cf = name.casefold()
        if cf in seen:
            continue
        seen.add(cf)
        out.append(name)
    return out


def _parse_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text else ""
    if "\t" not in first:
        raise ValueError(f"No TSV in {path}")
    cols = [c.strip().casefold() for c in first.split("\t")]
    if cols and cols[0] in ("bucket", "namingpool"):
        return _parse_bucket_tsv(path)
    return _parse_ranked_tsv(path)


def main() -> None:
    if not SRC_DIR.is_dir():
        raise SystemExit(f"Missing {SRC_DIR}")

    for fname, pool_name in FILE_TO_POOL:
        src = SRC_DIR / fname
        dst = POOL_DIR / pool_name
        if not src.is_file():
            raise SystemExit(f"Missing source {src}")
        if not dst.is_file():
            raise SystemExit(f"Missing pool {dst}")

        names = _parse_file(src)
        if not names:
            print(f"WARN: no names parsed from {fname}, skip")
            continue

        data = json.loads(dst.read_text(encoding="utf-8"))
        if "given_names_male" not in data:
            raise SystemExit(f"{pool_name} has no given_names_male")

        data["given_names_male"] = _tier_20_30_50_rest(names)
        dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{pool_name}: {len(names)} names -> tiers 20+30+50+{max(0, len(names) - 100)}")


if __name__ == "__main__":
    main()
