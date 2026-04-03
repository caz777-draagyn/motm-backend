"""
Create the six Nigeria regional custom name pools from Nigeria_6pool_expanded_big/.

Given tiers: 20 / 30 / 50 / rest. Surname tiers: 40 / 60 / 100 / rest.
SouthSouth CSVs map to custom_nigeriaDelta.

Re-run after updating the source CSVs:
  python scripts/build_nigeria_six_custom_pools.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Nigeria_6pool_expanded_big"
OUT_DIR = ROOT / "data" / "name_pools"

GIVEN_SLICES = (20, 30, 50)
SURNAME_SLICES = (40, 60, 100)

# (pool_id, country_name display, CSV basename prefix before _given_ / _surnames_)
POOL_SPECS: list[tuple[str, str, str]] = [
    ("custom_nigeriaIgbo", "Nigeria Igbo", "Nigeria_Igbo"),
    ("custom_nigeriaYoruba", "Nigeria Yoruba", "Nigeria_Yoruba"),
    ("custom_nigeriaHausa", "Nigeria Hausa", "Nigeria_Hausa"),
    ("custom_nigeriaFulani", "Nigeria Fulani", "Nigeria_Fulani"),
    ("custom_nigeriaMiddleBelt", "Nigeria Middle Belt", "Nigeria_MiddleBelt"),
    ("custom_nigeriaDelta", "Nigeria South-South (Delta)", "Nigeria_SouthSouth"),
]

DEFAULT_META = {
    "country_code": "NGA",
    "tier_probs": {
        "given": {
            "very_common": 0.55,
            "common": 0.3,
            "mid": 0.13,
            "rare": 0.02,
        },
        "surname": {
            "very_common": 0.45,
            "common": 0.35,
            "mid": 0.17,
            "rare": 0.03,
        },
    },
    "middle_name_prob": 0.08,
    "compound_surname_prob": 0.04,
    "surname_connector": "-",
}


def _norm_key(k: str) -> str:
    return k.replace("\ufeff", "").strip().lower().replace(" ", "_")


def _tier_split(names: list[str], slices: tuple[int, int, int]) -> dict[str, list[str]]:
    a, b, c = slices
    return {
        "very_common": names[:a],
        "common": names[a : a + b],
        "mid": names[a + b : a + b + c],
        "rare": names[a + b + c :],
    }


def _dedupe_preserve_order(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        k = n.casefold()
        if k in seen:
            continue
        seen.add(k)
        t = n.strip()
        if t:
            out.append(t)
    return out


def _load_csv_rank_name(path: Path, value_key: str) -> list[str]:
    rows: list[tuple[int, str]] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=",")
        if not reader.fieldnames:
            return []
        fm = {_norm_key(h): h for h in reader.fieldnames if h}
        val_col = fm.get(value_key) or fm.get("name") or fm.get("surname")
        rank_col = fm.get("rank")
        if not val_col:
            return []
        for row in reader:
            raw = (row.get(val_col) or "").strip()
            if not raw:
                continue
            if rank_col:
                try:
                    rk = int((row.get(rank_col) or "0").strip())
                except ValueError:
                    rk = 10**9
            else:
                rk = 10**9
            rows.append((rk, raw))
    rows.sort(key=lambda t: (t[0], t[1].casefold()))
    return _dedupe_preserve_order([n for _rk, n in rows])


def main() -> None:
    given_dir = SRC / "given"
    sur_dir = SRC / "surname"
    if not given_dir.is_dir() or not sur_dir.is_dir():
        print(f"Expected {given_dir} and {sur_dir}", file=sys.stderr)
        sys.exit(1)

    for pool_id, country_name, prefix in POOL_SPECS:
        g_path = given_dir / f"{prefix}_given_v2_big.csv"
        s_path = sur_dir / f"{prefix}_surnames_v2_big.csv"
        if not g_path.is_file():
            print(f"Missing given file: {g_path}", file=sys.stderr)
            sys.exit(1)
        if not s_path.is_file():
            print(f"Missing surname file: {s_path}", file=sys.stderr)
            sys.exit(1)

        given_list = _load_csv_rank_name(g_path, "name")
        sur_list = _load_csv_rank_name(s_path, "surname")
        if not given_list:
            print(f"No given names parsed: {g_path}", file=sys.stderr)
            sys.exit(1)
        if not sur_list:
            print(f"No surnames parsed: {s_path}", file=sys.stderr)
            sys.exit(1)

        data = {
            "pool_id": pool_id,
            "country_code": DEFAULT_META["country_code"],
            "country_name": country_name,
            "given_names_male": _tier_split(given_list, GIVEN_SLICES),
            "surnames": _tier_split(sur_list, SURNAME_SLICES),
            **{k: v for k, v in DEFAULT_META.items() if k != "country_code"},
        }

        out_path = OUT_DIR / f"{pool_id}.json"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(
            f"Wrote {out_path.name}: given={len(given_list)} surnames={len(sur_list)} "
            f"(vc/c/m/r given {len(data['given_names_male']['very_common'])}/"
            f"{len(data['given_names_male']['common'])}/"
            f"{len(data['given_names_male']['mid'])}/"
            f"{len(data['given_names_male']['rare'])})"
        )


if __name__ == "__main__":
    main()
