"""
Load reviewed surnames from finalSurname/*.csv, tier them (40 / 60 / 100 / rest),
and overwrite the `surnames` object in each data/name_pools country_*.json and custom_*.json.

Tier layout per pool:
- very_common: first 40 (by Country Rank ascending within ISO2)
- common: next 60
- mid: next 100
- rare: remainder

CSV files in finalSurname/ may use `;` (most regions) or `,` (e.g. South America export);
delimiter is detected from the header line.

Requires: pip install country_converter (FIFA 3-letter -> ISO 3166-1 alpha-2).
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_SURNAME_DIR = ROOT / "finalSurname"
NAME_POOLS_DIR = ROOT / "data" / "name_pools"

try:
    import country_converter as coco
except ImportError:  # pragma: no cover
    print("Install dependency: pip install country_converter", file=sys.stderr)
    raise

cc = coco.CountryConverter()

# country_converter does not know some FIFA codes used in this project
FIFA_TO_ISO2_FALLBACK: dict[str, str] = {
    "GBR": "GB",  # pool uses IOC-style code; surnames from UK resident stock
    "BRB": "BB",
    "EQG": "GQ",
    "GBZ": "GI",
    "GLP": "GP",
    "GUF": "GF",
    "LKA": "LK",
    "MMR": "MM",
    "MTQ": "MQ",
    "NIR": "GB",
    "SCO": "GB",
    "SIN": "SG",
    "TAH": "PF",
    "TTO": "TT",
    "WAL": "GB",
}

TIERS = ("very_common", "common", "mid", "rare")
SLICES = (40, 60, 100)  # counts for first three tiers


def _norm_fields(row: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in row.items():
        if not k:
            continue
        key = k.replace("\ufeff", "").strip().lower().replace(" ", "_")
        out[key] = (v or "").strip()
    return out


def _parse_rank(raw: str) -> int:
    raw = (raw or "").strip()
    if not raw:
        return 10**9
    try:
        return int(raw)
    except ValueError:
        return 10**9


def _male_ok(d: dict[str, str]) -> bool:
    v = (d.get("is_male_suitable") or "").lower()
    return v not in ("n", "no", "false")


def _final_keep(d: dict[str, str]) -> bool:
    return (d.get("final_status") or "").lower() == "keep"


def fifa_to_iso2(fifa: str) -> str | None:
    fifa = (fifa or "").strip().upper()
    if not fifa:
        return None
    if fifa in FIFA_TO_ISO2_FALLBACK:
        return FIFA_TO_ISO2_FALLBACK[fifa]
    try:
        out = cc.convert(fifa, src="FIFA", to="ISO2")
    except Exception:
        return None
    if not out or out == "not found":
        return None
    return str(out).upper()


def _detect_csv_delimiter(path: Path) -> str:
    """Prefer `;` (Europe/Asia/etc.) or `,` (South America exports) from first non-empty line."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        for _ in range(20):
            line = f.readline()
            if not line:
                break
            s = line.strip()
            if not s:
                continue
            return ";" if s.count(";") >= s.count(",") else ","
    return ";"


def load_surnames_by_iso2() -> dict[str, list[str]]:
    """ISO alpha-2 -> ordered unique surnames (best Country Rank wins on duplicates)."""
    best_rank: dict[str, dict[str, tuple[int, str]]] = defaultdict(
        dict
    )  # iso -> lower -> (rank, display_name)

    csv_paths = sorted(FINAL_SURNAME_DIR.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files under {FINAL_SURNAME_DIR}")

    for path in csv_paths:
        delim = _detect_csv_delimiter(path)
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=delim)
            for row in reader:
                d = _norm_fields(row)
                iso = (d.get("country_code") or "").upper()
                if not iso:
                    continue
                if not _final_keep(d) or not _male_ok(d):
                    continue
                name = (d.get("name") or "").strip()
                if not name:
                    continue
                rk = _parse_rank(d.get("country_rank"))
                key = name.casefold()
                prev = best_rank[iso].get(key)
                if prev is None or rk < prev[0]:
                    best_rank[iso][key] = (rk, name)

    out: dict[str, list[str]] = {}
    for iso, mp in best_rank.items():
        items = sorted(mp.values(), key=lambda t: (t[0], t[1].casefold()))
        out[iso] = [name for _rk, name in items]
    return out


def tier_from_ordered(names: list[str]) -> dict[str, list[str]]:
    n40, n60, n100 = SLICES
    a = names[:n40]
    b = names[n40 : n40 + n60]
    c = names[n40 + n60 : n40 + n60 + n100]
    r = names[n40 + n60 + n100 :]
    return {
        "very_common": a,
        "common": b,
        "mid": c,
        "rare": r,
    }


def main() -> None:
    by_iso = load_surnames_by_iso2()
    print(f"Loaded surname lists for {len(by_iso)} ISO2 regions from {FINAL_SURNAME_DIR.name}/")

    updated = 0
    skipped_no_iso = 0
    skipped_no_data = 0
    pool_files = sorted(NAME_POOLS_DIR.glob("country_*.json")) + sorted(
        NAME_POOLS_DIR.glob("custom_*.json")
    )

    for path in pool_files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip (read error): {path.name}: {e}")
            continue

        if "surnames" not in data or "country_code" not in data:
            continue

        fifa = str(data.get("country_code", "")).strip().upper()
        iso2 = fifa_to_iso2(fifa)
        if not iso2:
            print(f"No ISO2 mapping for FIFA {fifa}: {path.name}")
            skipped_no_iso += 1
            continue

        names = by_iso.get(iso2)
        if not names:
            skipped_no_data += 1
            continue

        data["surnames"] = tier_from_ordered(names)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        updated += 1

    print(f"Updated surnames in {updated} pools.")
    print(f"Skipped (no FIFA->ISO2): {skipped_no_iso}")
    print(f"Skipped (no CSV data for ISO2): {skipped_no_data}")


if __name__ == "__main__":
    main()
