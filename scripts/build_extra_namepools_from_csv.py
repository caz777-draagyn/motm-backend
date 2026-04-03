"""
One-off builder: extraNamepools/*.csv -> tiered JSON for country_ENG/NIR/SCO/WAL surnames
and custom_african_american / custom_french_canadian / custom_us_modern / custom_us_hispanic.

Run from repo root: python scripts/build_extra_namepools_from_csv.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
EXTRA = ROOT / "extraNamepools"
POOLS = ROOT / "data" / "name_pools"


def sniff_dialect(path: Path) -> csv.Dialect:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(8192)
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t,")
    except csv.Error:
        return csv.excel_tab


def split_surname_tiers(ordered_unique: List[str]) -> Dict[str, List[str]]:
    """Match scripts/deep_cleanse_surnames.split_into_tiers."""
    return {
        "very_common": ordered_unique[:40],
        "common": ordered_unique[40:100],
        "mid": ordered_unique[100:200],
        "rare": ordered_unique[200:],
    }


def load_uk_surnames_ordered(path: Path, name_field_candidates: Tuple[str, ...]) -> List[str]:
    d = sniff_dialect(path)
    seen: set[str] = set()
    out: List[str] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f, dialect=d)
        fields = [x for x in (r.fieldnames or []) if x]
        name_key = None
        for c in name_field_candidates:
            if c in fields:
                name_key = c
                break
        if not name_key:
            for fld in fields:
                low = fld.lower()
                if "name" in low or "surname" in low:
                    name_key = fld
                    break
        if not name_key:
            raise ValueError(f"No name column in {path}: {fields}")
        for row in r:
            n = (row.get(name_key) or "").strip()
            if not n:
                continue
            if n in seen:
                continue
            seen.add(n)
            out.append(n)
    return out


def read_tiered_givens(
    path: Path,
    tier_column: str,
    tier_to_bucket: Dict[str, str],
    name_column: str = "GivenName",
) -> Dict[str, List[str]]:
    d = sniff_dialect(path)
    rows: List[Tuple[int, str, str]] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f, dialect=d)
        for row in r:
            tier_raw = (row.get(tier_column) or "").strip()
            name = (row.get(name_column) or "").strip()
            if not name:
                continue
            bucket = tier_to_bucket.get(tier_raw)
            if not bucket:
                continue
            rank_s = (row.get("Rank") or "0").strip()
            try:
                rank = int(re.sub(r"[^\d]", "", rank_s) or 0)
            except ValueError:
                rank = 0
            rows.append((rank, bucket, name))
    rows.sort(key=lambda x: x[0])
    buckets: Dict[str, List[str]] = {k: [] for k in ("very_common", "common", "mid", "rare")}
    seen_global: set[str] = set()
    for _rank, bucket, name in rows:
        if name in seen_global:
            continue
        seen_global.add(name)
        buckets[bucket].append(name)
    return buckets


def default_meta(pool_id: str, country_code: str, country_name: str) -> Dict[str, Any]:
    return {
        "pool_id": pool_id,
        "country_code": country_code,
        "country_name": country_name,
        "tier_probs": {
            "given": {"very_common": 0.55, "common": 0.3, "mid": 0.13, "rare": 0.02},
            "surname": {"very_common": 0.45, "common": 0.35, "mid": 0.17, "rare": 0.03},
        },
        "middle_name_prob": 0.15,
        "compound_surname_prob": 0.05,
        "surname_connector": "-",
    }


def main() -> None:
    # --- UK surnames into existing country pools ---
    uk_map: List[Tuple[str, Path, Tuple[str, ...]]] = [
        ("ENG", EXTRA / "final_england_surnames.csv", ("Name_cleaned",)),
        ("NIR", EXTRA / "final_NorthernIreland_surname.csv", ("Name_cleaned",)),
        ("SCO", EXTRA / "Final_Scotland_surnames.csv", ("Surname",)),
        ("WAL", EXTRA / "final_Wales_surnames.csv", ("Name",)),
    ]
    for code, csv_path, name_cols in uk_map:
        if not csv_path.is_file():
            raise FileNotFoundError(csv_path)
        names = load_uk_surnames_ordered(csv_path, name_cols)
        sur = split_surname_tiers(names)
        jpath = POOLS / f"country_{code}.json"
        with open(jpath, encoding="utf-8") as f:
            data = json.load(f)
        data["surnames"] = sur
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Updated {jpath.name} surnames: {len(names)} unique -> tiers {len(sur['very_common'])}/{len(sur['common'])}/{len(sur['mid'])}/{len(sur['rare'])}")

    fc_givens = read_tiered_givens(
        EXTRA / "FrenchCanadian_given_names.csv",
        "RarityLayer",
        {
            "top_20_very_common": "very_common",
            "21_50_common": "common",
            "51_100_normal": "mid",
            "101_plus_rare": "rare",
        },
    )
    fc_surnames_raw = read_tiered_givens(
        EXTRA / "FrenchCanadian_surnames_expanded.csv",
        "RarityLayer",
        {
            "top_20_very_common": "very_common",
            "21_50_common": "common",
            "51_100_normal": "mid",
            "101_plus_rare": "rare",
        },
        name_column="Surname",
    )

    aa_givens = read_tiered_givens(
        EXTRA / "AfricanAmerican_male_given_names_expanded.csv",
        "Tier",
        {
            "core_common": "very_common",
            "common_overlap": "common",
            "stylized_distinctive": "mid",
            "rarer_but_plausible": "rare",
        },
    )

    us_modern = read_tiered_givens(
        EXTRA / "US_modern_mainstream_given_names.csv",
        "RarityLayer",
        {
            "top_20_very_common": "very_common",
            "21_50_common": "common",
            "51_100_normal": "mid",
            "101_plus_rare": "rare",
        },
    )

    us_hisp = read_tiered_givens(
        EXTRA / "US_Hispanic_Chicano_given_names.csv",
        "RarityLayer",
        {
            "top_20_very_common": "very_common",
            "21_50_common": "common",
            "51_100_normal": "mid",
            "101_plus_rare": "rare",
        },
    )

    custom_specs: List[Tuple[str, str, str, Dict[str, List[str]], str | None]] = [
        ("custom_african_american.json", "USA", "United States (African American)", aa_givens, "country_USA"),
        ("custom_french_canadian.json", "CAN", "Canada (French Canadian)", fc_givens, None),
        ("custom_us_modern.json", "USA", "United States (modern mainstream)", us_modern, "country_USA"),
        ("custom_us_hispanic.json", "USA", "United States (Hispanic / Chicano)", us_hisp, "country_USA"),
    ]

    for fname, cc, cname, giv, inherit_usa in custom_specs:
        out = default_meta(fname.replace(".json", ""), cc, cname)
        out["given_names_male"] = giv
        if inherit_usa:
            out["surname_inherit_pool_id"] = inherit_usa
        else:
            out["surnames"] = fc_surnames_raw
        outp = POOLS / fname
        with open(outp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        tg = sum(len(v) for v in giv.values())
        extra = f"surnames inherit {inherit_usa}" if inherit_usa else "inline surnames"
        print(f"Wrote {outp.name}: {tg} given ({extra})")


if __name__ == "__main__":
    main()
