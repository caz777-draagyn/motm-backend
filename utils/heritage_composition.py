"""
Load FullHeritageAndNamingComposition (tab-separated) and merge into HERITAGE_CONFIG.

Also builds COUNTRY_FEDERATION (country code -> confederation string like UEFA).

Profile art is expected under: gfx/player_profile_pics/<VisualBucket>/
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_BASE = Path(__file__).resolve().parent.parent
_COMPOSITION_DIR = _BASE / "data" / "heritage_composition"
_COMPOSITION_FILE = _COMPOSITION_DIR / "FullHeritageAndNamingComposition.txt"
_NAME_POOLS_DIR = _BASE / "data" / "name_pools"

# region -> federation code (strip spaces)
REGION_TO_FEDERATION = {
    "UEFA": "UEFA",
    "CONMEBOL": "CONMEBOL",
    "CONCACAF": "CONCACAF",
    "CAF": "CAF",
    "AFC": "AFC",
    "OFC": "OFC",
    "FIFA": "FIFA",
}

# ---------------------------------------------------------------------------
# Display name -> FIFA-like codes used by name_pools + composition-only nations
# ---------------------------------------------------------------------------
_POOL_LABEL_OVERRIDES: Dict[str, str] = {}
_COUNTRY_DISPLAY_OVERRIDES: Dict[str, str] = {}


def _norm(s: str) -> str:
    return s.strip().lower()


def _build_pool_name_to_code() -> Dict[str, str]:
    m: Dict[str, str] = {}
    if not _NAME_POOLS_DIR.is_dir():
        return m
    for fp in sorted(_NAME_POOLS_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        code = data.get("country_code")
        name = data.get("country_name")
        if code and name:
            m[_norm(name)] = code
    # Pool labels that differ from pool country_name
    overrides = {
        "england": "ENG",
        "scotland": "SCO",
        "wales": "WAL",
        "northern ireland": "NIR",
        "ivory coast": "CIV",
        "dr congo": "COD",
        "congo": "CGO",
        "czech republic": "CZE",
        "turkey": "TUR",
        "united states": "USA",
        "south korea": "KOR",
        "north macedonia": "MKD",
        "bosnia and herzegovina": "BIH",
        "trinidad and tobago": "TTO",
        "cape verde": "CPV",
        "united arab emirates": "UAE",
        "faroe islands": "FRO",
        "belgium dutch": "BEL",
        "belgium french": "BEL",
        "catalan": "ESP",
        "catalanl": "ESP",
        "pays basque": "ESP",
        "german": "GER",
        "germany": "GER",
        "china north": "CHN",
        "china south": "CHN",
        "pakistan punjabi": "PAK",
        "pakistan pashtun": "PAK",
        "pakistan sindhi": "PAK",
        "india punjabi": "IND",
        "india gangetic": "IND",
        "india bengali": "IND",
        "tamil": "IND",
        "telugu": "IND",
        "kannada": "IND",
        "malaylam": "IND",
        "malayalam": "IND",
        "french caribbean": "FRA",
        "dutch caribbean": "NED",
        "suriname hindustani": "SUR",
        "suriname": "SUR",
        "afghanistan dari": "AFG",
        "israel hebrew": "ISR",
        "fiji indian": "FIJ",
        "fiji indigenous": "FIJ",
        "indonesia javanese": "IDN",
        "indonesia sumatran": "IDN",
        "indonesia other": "IDN",
        "swiss german": "SUI",
        "swiss french": "SUI",
        "swiss italian": "SUI",
        "cambodia": "CAM",
        "myanmar": "MMR",
        "new caledonia": "NCL",
        "malaysia chinese": "MAS",
        "malaysia indian": "MAS",
        "malaysia malay": "MAS",
        "melanesia": "PNG",
        "gibraltar": "GBR",
        "tahiti": "TAH",
        "tāhiti": "TAH",
        "new zealand māori": "NZL",
        "philippines tagalog": "PHI",
        "philippines visayan": "PHI",
        "polynesia": "TAH",
        "puerto rico": "USA",
        "samoa": "SAM",
        "singapore chinese": "SIN",
        "singapore indian": "SIN",
        "singapore malay": "SIN",
        "solomon islands": "SOL",
        "sri lanka sinhala": "LKA",
        "tajikistan": "TJK",
        "tonga": "TGA",
        "vanuatu": "VAN",
        "uae": "UAE",
        "cook islands": "COK",
    }
    for k, v in overrides.items():
        m[k] = v
    m.update(_POOL_LABEL_OVERRIDES)
    return m


def _build_country_display_to_code() -> Dict[str, str]:
    m = _build_pool_name_to_code().copy()  # country_name entries + overrides keys overlap
    country_ovr = {
        "england": "ENG",
        "scotland": "SCO",
        "wales": "WAL",
        "northern ireland": "NIR",
        "united states": "USA",
        "south korea": "KOR",
        "ivory coast": "CIV",
        "dr congo": "COD",
        "congo": "CGO",
        "north macedonia": "MKD",
        "bosnia and herzegovina": "BIH",
        "trinidad and tobago": "TTO",
        "cape verde": "CPV",
        "united arab emirates": "UAE",
        "american samoa": "ASA",
        "andorra": "AND",
        "aruba": "ARU",
        "barbados": "BRB",
        "bhutan": "BHU",
        "botswana": "BOT",
        "british virgin islands": "VGB",
        "burundi": "BDI",
        "cambodia": "CAM",
        "cayman islands": "CAY",
        "central african republic": "CTA",
        "chad": "CHA",
        "cook islands": "COK",
        "curaçao": "CUW",
        "djibouti": "DJI",
        "equatorial guinea": "EQG",
        "eritrea": "ERI",
        "faroe islands": "FRO",
        "fiji": "FIJ",
        "french guiana": "GUF",
        "gabon": "GAB",
        "gambia": "GAM",
        "gibraltar": "GBZ",
        "grenada": "GRN",
        "guadeloupe": "GLP",
        "guam": "GUM",
        "guinea-bissau": "GNB",
        "guyana": "GUY",
        "kyrgyzstan": "KGZ",
        "laos": "LAO",
        "malawi": "MWI",
        "maldives": "MDV",
        "martinique": "MTQ",
        "mauritania": "MTN",
        "mongolia": "MNG",
        "montenegro": "MNE",
        "myanmar": "MMR",
        "namibia": "NAM",
        "new caledonia": "NCL",
        "niger": "NIG",
        "puerto rico": "USA",
        "saint lucia": "LCA",
        "samoa": "SAM",
        "san marino": "SMR",
        "sierra leone": "SLE",
        "solomon islands": "SOL",
        "south sudan": "SSD",
        "são tomé and príncipe": "STP",
        "sao tome and principe": "STP",
        "tahiti": "TAH",
        "tāhiti": "TAH",
        "tajikistan": "TJK",
        "togo": "TOG",
        "tonga": "TGA",
        "turkmenistan": "TKM",
        "us virgin islands": "VIR",
        "vanuatu": "VAN",
        "yemen": "YEM",
        "bermuda": "BER",
        "cook islands": "COK",
    }
    for k, v in country_ovr.items():
        m[k] = v
    m.update(_COUNTRY_DISPLAY_OVERRIDES)
    return m


def pool_label_to_code(label: str, pool_map: Dict[str, str]) -> Optional[str]:
    raw = label.strip()
    key = _norm(raw)
    if key in pool_map:
        return pool_map[key]
    # drop parenthetical
    key2 = re.sub(r"\s*\([^)]*\)\s*", "", key).strip()
    if key2 in pool_map:
        return pool_map[key2]
    return None


def parse_pool_weights(s: str, pool_map: Dict[str, str]) -> Dict[str, float]:
    """Parse 'Norway 0.88, Denmark 0.07' into { 'NOR': 0.88, 'DEN': 0.07 }."""
    out: Dict[str, float] = {}
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s+([\d.]+)\s*$", part)
        if not m:
            continue
        label, wt_s = m.group(1).strip(), m.group(2)
        code = pool_label_to_code(label, pool_map)
        if not code:
            continue
        try:
            out[code] = float(wt_s)
        except ValueError:
            continue
    return out


_STRUCTURE_RE = re.compile(
    r"(LOCAL_LOCAL|LOCAL_HERITAGE|HERITAGE_LOCAL|HERITAGE_HERITAGE|"
    r"DOUBLE_SURNAME_LOCAL_LOCAL|COMPOUND_GIVEN_LOCAL_LOCAL)\s+([\d.]+)",
    re.I,
)


def parse_naming_split(s: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Returns:
      name_structure_probs: LL/LH/HL/HH weights (normalized)
      composition_extras: weights for LL_DOUBLE_SURNAME, LL_COMPOUND_GIVEN (of total roll)
    """
    structs: Dict[str, float] = {}
    extras: Dict[str, float] = {}
    for name, wt in _STRUCTURE_RE.findall(s or ""):
        n = name.upper()
        try:
            w = float(wt)
        except ValueError:
            continue
        if n == "DOUBLE_SURNAME_LOCAL_LOCAL":
            extras["LL_DOUBLE_SURNAME"] = extras.get("LL_DOUBLE_SURNAME", 0) + w
        elif n == "COMPOUND_GIVEN_LOCAL_LOCAL":
            extras["LL_COMPOUND_GIVEN"] = extras.get("LL_COMPOUND_GIVEN", 0) + w
        elif n == "LOCAL_LOCAL":
            structs["LL"] = structs.get("LL", 0) + w
        elif n == "LOCAL_HERITAGE":
            structs["LH"] = structs.get("LH", 0) + w
        elif n == "HERITAGE_LOCAL":
            structs["HL"] = structs.get("HL", 0) + w
        elif n == "HERITAGE_HERITAGE":
            structs["HH"] = structs.get("HH", 0) + w
    tot = sum(structs.values()) + sum(extras.values())
    if tot > 0:
        for d in (structs, extras):
            for k in list(d.keys()):
                d[k] = d[k] / tot
    return structs, extras


def load_composition_rows() -> List[Dict[str, Any]]:
    if not _COMPOSITION_FILE.is_file():
        return []
    text = _COMPOSITION_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 2:
        return []
    pool_map = _build_pool_name_to_code()
    country_map = _build_country_display_to_code()
    rows: List[Dict[str, Any]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        region, country_disp, visual_bucket, pct_s, naming_pool_s, naming_split = parts[:6]
        fed = REGION_TO_FEDERATION.get(region.strip(), region.strip())
        cc = country_map.get(_norm(country_disp))
        if not cc:
            continue
        try:
            pct = float(pct_s)
        except ValueError:
            continue
        origin_weights = parse_pool_weights(naming_pool_s, pool_map)
        struct_probs, extra_probs = parse_naming_split(naming_split)
        rows.append(
            {
                "federation": fed,
                "country_display": country_disp.strip(),
                "nationality_code": cc,
                "visual_bucket": visual_bucket.strip(),
                "percent": pct,
                "origin_country_weights": origin_weights,
                "name_structure_probs": struct_probs,
                "composition_extras": extra_probs,
            }
        )
    return rows


def build_country_federation(rows: List[Dict[str, Any]]) -> Dict[str, str]:
    """First row per nationality wins federation."""
    out: Dict[str, str] = {}
    for r in rows:
        c = r["nationality_code"]
        if c not in out:
            out[c] = r["federation"]
    return out


def build_heritage_groups_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """nationality_code -> { group_key -> heritage config }."""
    by_nat: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_nat.setdefault(r["nationality_code"], []).append(r)

    heritage: Dict[str, Dict[str, Any]] = {}
    for nat, lst in by_nat.items():
        wsum = sum(x["percent"] for x in lst) or 1.0
        groups: Dict[str, Any] = {}
        for r in lst:
            vb = re.sub(r"[^A-Za-z0-9_]+", "_", r["visual_bucket"]).strip("_")
            gkey = f"{nat}_{vb}"
            rel_pic = f"player_profile_pics/{r['visual_bucket']}"
            ow = r["origin_country_weights"]
            if not ow:
                ow = {nat: 1.0}
            groups[gkey] = {
                "weight": r["percent"] / wsum,
                "picture_folder": rel_pic,
                "origin_country_weights": ow,
                "name_structure_probs": r["name_structure_probs"],
                "composition_extras": r["composition_extras"],
                "visual_bucket": r["visual_bucket"],
                "composition_source": "FullHeritageAndNamingComposition",
            }
        heritage[nat] = groups
    return heritage


def apply_to_name_data() -> Tuple[int, int]:
    """
    Merge composition into globals in utils.name_data.
    Returns (countries_updated, rows_loaded).
    """
    from . import name_data

    rows = load_composition_rows()
    if not rows:
        return 0, 0

    fed = build_country_federation(rows)
    name_data.COUNTRY_FEDERATION.clear()
    name_data.COUNTRY_FEDERATION.update(fed)

    groups_by_nat = build_heritage_groups_from_rows(rows)
    n = 0
    for nat, groups in groups_by_nat.items():
        name_data.HERITAGE_CONFIG[nat] = groups
        n += 1

    # Refresh picture-folder map so replaced nationalities do not leave stale group keys
    name_data.HERITAGE_PICTURE_FOLDER_MAP.clear()
    for _nat, groups in name_data.HERITAGE_CONFIG.items():
        for gkey, cfg in groups.items():
            if cfg.get("picture_folder"):
                name_data.HERITAGE_PICTURE_FOLDER_MAP[gkey] = cfg["picture_folder"]

    _write_country_federation_json(fed)
    return n, len(rows)


def _write_country_federation_json(fed: Dict[str, str]) -> None:
    path = _BASE / "data" / "country_federation.json"
    text = json.dumps(dict(sorted(fed.items())), indent=2, ensure_ascii=False) + "\n"
    try:
        if path.is_file():
            existing = path.read_text(encoding="utf-8")
            if existing == text:
                return
        path.write_text(text, encoding="utf-8")
    except OSError:
        pass
