"""
Load male given names from Custom_firstname/ and surnames from Custom_surname/
into the matching data/name_pools/*.json files.

Given-name tiers: very_common 20, common 30, mid 50, rare = remainder (file order / Rank).
Surname tiers: very_common 40, common 60, mid 100, rare = remainder.

Preserves existing JSON keys other than given_names_male / surnames (tier_probs, pool_id, etc.).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST_DIR = ROOT / "Custom_firstname"
SUR_DIR = ROOT / "Custom_surname"
POOLS_DIR = ROOT / "data" / "name_pools"

GIVEN_SLICES = (20, 30, 50)
SURNAME_SLICES = (40, 60, 100)
TIERS = ("very_common", "common", "mid", "rare")

# basename -> pool JSON filename under data/name_pools/
FIRSTNAME_FILES: dict[str, str] = {
    "Singapore_Malay_given_expanded2.csv": "custom_singapore_malay.json",
    "Malaysia_Malay_given_expanded2.csv": "custom_malaysia_malay.json",
    "Singapore_Chinese_given_expanded2.csv": "custom_singapore_chinese.json",
    "Malaysia_Chinese_given_expanded2.csv": "custom_malaysia_chinese.json",
    "Fiji_Indo_given_expanded.csv": "custom_fiji_indian.json",
    "Fiji_Indigenous_given_expanded.csv": "custom_fiji_indigenous.json",
    "Pakistan_Sindhi_given_expanded.csv": "custom_pakistan_sindhi.json",
    "Pakistan_Punjabi_given_expanded.csv": "custom_pakistan_punjabi.json",
    "Pakistan_Pashtun_given_expanded.csv": "custom_pakistan_pashtun.json",
    "Bengali_male_given_names_estimated.csv": "custom_india_bengali.json",
    "India_N_Gangetic_male_given_names_estimated.csv": "custom_india_gangetic.json",
    "India_Punjabi_NW_male_given_names_estimated.csv": "custom_india_punjabi.json",
    "Kannada_male_given_names_estimated.csv": "custom_kannada.json",
    "Malayalam_male_given_names_estimated.csv": "custom_malaylam.json",
    "Sinhalese_male_given_names_estimated.csv": "custom_sri_lanka_sinhala.json",
    "Tamil_male_given_names_estimated.csv": "custom_tamil.json",
    "Telugu_male_given_names_estimated.csv": "custom_telugu.json",
    "New_Caledonia_male_given_names_estimated.csv": "country_NCL.json",
    "Tonga_male_given_names_estimated.csv": "country_TGA.json",
    "Solomon_Islands_male_given_names_estimated.csv": "country_SOL.json",
    "Vanuatu_male_given_names_estimated.csv": "country_VAN.json",
    "Samoa_male_given_names_estimated.csv": "country_SAM.json",
    "Puerto_Rico_male_given_names_estimated_300.csv": "custom_puerto_rico.json",
    "Gibraltar_male_given_names_estimated_180.csv": "custom_gibraltar.json",
    "Cambodia_male_given_names_estimated_300.csv": "country_CAM.json",
    "final_catalan.txt": "custom_catalan.json",
    "final_Basque.txt": "custom_pays_basque.json",
    "final_scotland.txt": "country_SCO.json",
    "final_northIreland.txt": "country_NIR.json",
    "final_wales.txt": "country_WAL.json",
    "Final_England.txt": "country_ENG.json",
    "swissGerman.txt": "custom_swiss_german.json",
    "swissFrench.txt": "custom_swiss_french.json",
    "swissItalian.txt": "custom_swiss_italian.json",
    "Final_BelgiumFrench.txt": "custom_belgium_french.json",
    "Final_BelgiumDutch.txt": "custom_belgium_dutch.json",
}

SURNAME_FILES: dict[str, str] = {
    "Singapore_Chinese_surnames_expanded2.csv": "custom_singapore_chinese.json",
    "Malaysia_Chinese_surnames_expanded2.csv": "custom_malaysia_chinese.json",
    "Singapore_Malay_surnames_expanded2.csv": "custom_singapore_malay.json",
    "Malaysia_Malay_surnames_expanded2.csv": "custom_malaysia_malay.json",
    "Fiji_Indo_surnames_expanded.csv": "custom_fiji_indian.json",
    "Fiji_Indigenous_surnames_expanded.csv": "custom_fiji_indigenous.json",
    "Pakistan_Sindhi_surnames_expanded.csv": "custom_pakistan_sindhi.json",
    "Pakistan_Punjabi_surnames_expanded.csv": "custom_pakistan_punjabi.json",
    "Pakistan_Pashtun_surnames_expanded.csv": "custom_pakistan_pashtun.json",
    "Tamil_expanded_surnames_high_confidence.csv": "custom_tamil.json",
    "Telugu_expanded_surnames_high_confidence.csv": "custom_telugu.json",
    "Bengali_surnames_high_confidence.csv": "custom_india_bengali.json",
    "India_N_Gangetic_surnames_high_confidence.csv": "custom_india_gangetic.json",
    "India_Punjabi_NW_surnames_high_confidence.csv": "custom_india_punjabi.json",
    "Kannada_surnames_high_confidence.csv": "custom_kannada.json",
    "Malayalam_surnames_high_confidence.csv": "custom_malaylam.json",
    "Sinhalese_surnames_high_confidence.csv": "custom_sri_lanka_sinhala.json",
    "Gibraltar_surnames_high_confidence.csv": "custom_gibraltar.json",
    "Puerto_Rico_surnames_high_confidence.csv": "custom_puerto_rico.json",
    "Cambodia_surnames_high_confidence.csv": "country_CAM.json",
    "New_Caledonia_surnames_high_confidence.csv": "country_NCL.json",
    "Tonga_surnames_high_confidence.csv": "country_TGA.json",
    "Samoa_surnames_high_confidence.csv": "country_SAM.json",
    "Solomon_Islands_surnames_high_confidence.csv": "country_SOL.json",
    "Vanuatu_surnames_high_confidence.csv": "country_VAN.json",
    "final_BasqueSurname.txt": "custom_pays_basque.json",
    "final_CatalanSurname.txt": "custom_catalan.json",
}


def _norm_key(k: str) -> str:
    return k.replace("\ufeff", "").strip().lower().replace(" ", "_")


def _tier_split(names: list[str], slices: tuple[int, int, int]) -> dict[str, list[str]]:
    a, b, c = slices
    vc = names[:a]
    co = names[a : a + b]
    mi = names[a + b : a + b + c]
    ra = names[a + b + c :]
    return {"very_common": vc, "common": co, "mid": mi, "rare": ra}


def _dedupe_preserve_order(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        k = n.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(n.strip())
    return [x for x in out if x]


def _load_csv_ordered(path: Path, value_field: str) -> list[str]:
    """value_field: 'name' or 'surname' — picks column whose normalized header matches."""
    rows: list[tuple[int, str]] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=",")
        if not reader.fieldnames:
            return []
        field_map = {_norm_key(h): h for h in reader.fieldnames if h}
        # resolve value column
        val_col = None
        for cand in (value_field, "name", "surname"):
            if cand in field_map:
                val_col = field_map[cand]
                break
        if not val_col:
            return []
        rank_col = None
        for key in ("rank",):
            if key in field_map:
                rank_col = field_map[key]
                break
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
    ordered = [n for _rk, n in rows]
    return _dedupe_preserve_order(ordered)


def _split_tab_line(line: str) -> list[str]:
    return [p.strip() for p in line.split("\t")]


def _load_txt_ordered(path: Path, prefer_name_keys: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    header_parts = _split_tab_line(lines[0])
    hdr = [_norm_key(h) for h in header_parts]
    # column index for name / surname
    idx_val = None
    idx_rank = None
    for i, h in enumerate(hdr):
        if h in prefer_name_keys or h in ("name", "surname"):
            idx_val = i
            break
    if idx_val is None:
        # England-style: first column is Name
        if hdr and hdr[0] == "name":
            idx_val = 0
        else:
            idx_val = 0
    for i, h in enumerate(hdr):
        if h == "rank":
            idx_rank = i
            break
    rows: list[tuple[int, str]] = []
    for order, line in enumerate(lines[1:], start=1):
        parts = _split_tab_line(line)
        if idx_val >= len(parts):
            continue
        raw = parts[idx_val].strip()
        if not raw:
            continue
        if idx_rank is not None and idx_rank < len(parts):
            try:
                rk = int(re.sub(r"[^\d]", "", parts[idx_rank]) or "0") or order
            except ValueError:
                rk = order
        else:
            rk = order
        rows.append((rk, raw))
    rows.sort(key=lambda t: (t[0], t[1].casefold()))
    return _dedupe_preserve_order([n for _rk, n in rows])


def load_given_path(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        return _load_csv_ordered(path, "name")
    return _load_txt_ordered(path, ("name",))


def load_surname_path(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        return _load_csv_ordered(path, "surname")
    return _load_txt_ordered(path, ("surname",))


def main() -> None:
    updates: dict[Path, dict] = {}

    def ensure_pool(json_name: str) -> dict:
        p = POOLS_DIR / json_name
        if p not in updates:
            if not p.is_file():
                print(f"Missing pool file: {p}")
                return {}
            with open(p, encoding="utf-8") as f:
                updates[p] = json.load(f)
        return updates[p]

    n_first = n_sur = 0
    for base, json_name in FIRSTNAME_FILES.items():
        src = FIRST_DIR / base
        if not src.is_file():
            print(f"Missing firstname source: {src}")
            continue
        data = ensure_pool(json_name)
        if not data:
            continue
        names = load_given_path(src)
        if not names:
            print(f"No names parsed: {src}")
            continue
        data["given_names_male"] = _tier_split(names, GIVEN_SLICES)
        n_first += 1
        print(f"given {base} -> {json_name} ({len(names)} names)")

    for base, json_name in SURNAME_FILES.items():
        src = SUR_DIR / base
        if not src.is_file():
            print(f"Missing surname source: {src}")
            continue
        data = ensure_pool(json_name)
        if not data:
            continue
        names = load_surname_path(src)
        if not names:
            print(f"No surnames parsed: {src}")
            continue
        data["surnames"] = _tier_split(names, SURNAME_SLICES)
        n_sur += 1
        print(f"surname {base} -> {json_name} ({len(names)} names)")

    for path, data in updates.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    print(f"\nWrote {len(updates)} pool file(s); {n_first} given updates, {n_sur} surname updates.")


if __name__ == "__main__":
    main()
