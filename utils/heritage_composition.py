"""
Load FullHeritageAndNamingComposition (tab-separated) and merge into HERITAGE_CONFIG.

The composition file is the primary design input. Preferred format (tab-separated):

  Region \\t NationalityCode \\t Country \\t VisualBucket \\t percent \\t naming pool \\t naming split

- **NationalityCode**: 3-letter FIFA-style code (e.g. ISL, ATG). This is the authoritative
  link from each row to in-game nationality; **Country** is the human display name only.

Legacy 6-column files (no NationalityCode) are still supported: Country is resolved to a
code via name-pool JSON `country_name` / `country_code` plus `_build_country_display_to_code`
overrides (silent skip if unmapped).

Also builds COUNTRY_FEDERATION (country code -> confederation string like UEFA).

Naming split (last column) may use **NATION_*** tokens (e.g. NATION_NATION, NATION_HERITAGE) or
**LOCAL_*** — both map to the same LL/LH/HL/HH probabilities in parse_naming_split.

Profile art is expected under: gfx/player_profile_pics/<VisualBucket>/
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from collections import defaultdict
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
    seen: set[Path] = set()
    for pattern in ("country_*.json", "custom_*.json", "*.json"):
        for fp in sorted(_NAME_POOLS_DIR.glob(pattern)):
            if fp in seen:
                continue
            seen.add(fp)
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
        "puerto rico": "PUR",
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


def _build_label_to_pool_id() -> Dict[str, str]:
    """
    Map normalized country_name from each pool JSON -> pool_id (country_* or custom_*).

    **Country pools win:** `country_*.json` labels are registered first. `custom_*.json` only
    adds a label if that normalized name is not already taken. That way a plain country name
    (e.g. Wales) resolves to `country_WAL` when present, while sub-national / cultural pools
    (e.g. Belgium Dutch) keep distinct labels.
    """
    m: Dict[str, str] = {}
    if not _NAME_POOLS_DIR.is_dir():
        return m

    def _ingest_files(pattern: str, seen: set[Path], fill_gaps_only: bool) -> None:
        for fp in sorted(_NAME_POOLS_DIR.glob(pattern)):
            if fp in seen:
                continue
            seen.add(fp)
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            code = data.get("country_code")
            name = data.get("country_name")
            if not code or not name:
                continue
            pid = data.get("pool_id") or f"country_{code}"
            key = _norm(name)
            if fill_gaps_only:
                if key in m:
                    continue
            m[key] = pid

    seen_paths: set[Path] = set()
    _ingest_files("country_*.json", seen_paths, fill_gaps_only=False)
    _ingest_files("custom_*.json", seen_paths, fill_gaps_only=True)
    _ingest_files("*.json", seen_paths, fill_gaps_only=True)
    # Composition uses compact labels (no spaces) or marketing names; map to real pool_id.
    for k, v in _composition_label_to_pool_id().items():
        if k not in m:
            m[k] = v
    return m


def _composition_label_to_pool_id() -> Dict[str, str]:
    """
    Extra label (normalized) -> pool_id for strings in the composition "naming pool" column
    that are not exactly the JSON country_name.
    """
    return {
        # Nigeria regional (composition uses camelCase / no space)
        "nigeriayoruba": "custom_nigeriaYoruba",
        "nigeriaigbo": "custom_nigeriaIgbo",
        "nigeriadelta": "custom_nigeriaDelta",
        "nigeriahausa": "custom_nigeriaHausa",
        "nigeriamiddlebelt": "custom_nigeriaMiddleBelt",
        "nigeriafulani": "custom_nigeriaFulani",
        # Plain labels in TSV naming-pool column (pool JSON may also set country_name)
        "philippines": "custom_philippines",
        "swiss": "custom_swiss",
        "switzerland": "custom_swiss",
        # US / Canada custom pools
        "frenchcanadian": "custom_french_canadian",
        "usmodern": "custom_us_modern",
        "ushispanic": "custom_us_hispanic",
        "usafricanamerican": "custom_african_american",
        # India — "India South" used as macro-region; Tamil Nadu–centric until a dedicated pool exists
        "india south": "custom_tamil",
    }


def _build_pool_id_to_country_code() -> Dict[str, str]:
    """pool_id -> FIFA country_code (tier / connector lookup)."""
    m: Dict[str, str] = {}
    if not _NAME_POOLS_DIR.is_dir():
        return m
    seen: set[Path] = set()
    for pattern in ("country_*.json", "custom_*.json", "*.json"):
        for fp in sorted(_NAME_POOLS_DIR.glob(pattern)):
            if fp in seen:
                continue
            seen.add(fp)
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            code = data.get("country_code")
            if not code:
                continue
            pid = data.get("pool_id") or f"country_{code}"
            m[pid] = code
    return m


def _rollup_pool_weights_to_fifa(
    pool_weights: Dict[str, float], pool_id_to_cc: Dict[str, str]
) -> Dict[str, float]:
    """Merge custom_* pools into FIFA buckets for legacy / analytics."""
    out: Dict[str, float] = defaultdict(float)
    for pid, w in pool_weights.items():
        cc = pool_id_to_cc.get(pid)
        if not cc and pid.startswith("country_"):
            cc = pid[len("country_") :]
        if cc:
            out[cc] += w
    return dict(out)


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
        "puerto rico": "PUR",
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
        "antigua and barbuda": "ATG",
        # Additional display names used in composition before matching name-pool files exist
        "brunei": "BRU",
        "comoros": "COM",
        "dominica": "DMA",
        "eswatini": "SWZ",
        "kiribati": "KIR",
        "lesotho": "LES",
        "liechtenstein": "LIE",
        "madagascar": "MAD",
        "marshall islands": "MHL",
        "mauritius": "MRI",
        "micronesia": "FSM",
        "nauru": "NRU",
        "palau": "PLW",
        "saint kitts and nevis": "SKN",
        "saint vincent and the grenadines": "VIN",
        "seychelles": "SEY",
        "tuvalu": "TUV",
        # FIFA national teams: composition Country column must resolve even when there is no
        # generic country_<code>.json (regional naming uses custom_* pools in local_core / TSV).
        "belgium": "BEL",
        "switzerland": "SUI",
        "india": "IND",
        "nigeria": "NGA",
        "pakistan": "PAK",
        "singapore": "SIN",
        "sri lanka": "LKA",
        "indonesia": "IDN",
        "malaysia": "MAS",
        "philippines": "PHI",
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


def parse_pool_weights(
    s: str, pool_map: Dict[str, str], label_to_pool_id: Dict[str, str]
) -> Dict[str, float]:
    """
    Parse 'Norway 0.88, Belgium Dutch 0.42' into pool_id -> weight
    (e.g. country_NOR, custom_belgium_dutch). Labels resolve via name-pool JSON country_name,
    then pool_label_to_code -> country_XXX.
    """
    out: Dict[str, float] = {}
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s+([\d.]+)\s*$", part)
        if not m:
            continue
        label, wt_s = m.group(1).strip(), m.group(2)
        key = _norm(label)
        pid = label_to_pool_id.get(key)
        if not pid:
            key2 = re.sub(r"\s*\([^)]*\)\s*", "", key).strip()
            pid = label_to_pool_id.get(key2)
        if not pid:
            code = pool_label_to_code(label, pool_map)
            if code:
                pid = f"country_{code}"
        if not pid:
            continue
        try:
            w = float(wt_s)
        except ValueError:
            continue
        out[pid] = out.get(pid, 0.0) + w
    return out


def parse_pool_weights_unresolved(
    s: str, pool_map: Dict[str, str], label_to_pool_id: Dict[str, str]
) -> Tuple[Dict[str, float], List[str]]:
    """
    Same as parse_pool_weights, but also returns labels that did not resolve to any pool_id.
    """
    out: Dict[str, float] = {}
    unresolved: List[str] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s+([\d.]+)\s*$", part)
        if not m:
            unresolved.append(part)
            continue
        label, wt_s = m.group(1).strip(), m.group(2)
        key = _norm(label)
        pid = label_to_pool_id.get(key)
        if not pid:
            key2 = re.sub(r"\s*\([^)]*\)\s*", "", key).strip()
            pid = label_to_pool_id.get(key2)
        if not pid:
            code = pool_label_to_code(label, pool_map)
            if code:
                pid = f"country_{code}"
        if not pid:
            unresolved.append(label)
            continue
        try:
            w = float(wt_s)
        except ValueError:
            unresolved.append(label)
            continue
        out[pid] = out.get(pid, 0.0) + w
    return out, unresolved


# Naming split: only LL/LH/HL/HH (LOCAL_* or NATION_* / HERITAGE_*).
# Middle name and compound surname come from each name pool JSON, not the composition row.
_STRUCTURE_RE = re.compile(
    r"(LOCAL_LOCAL|NATION_NATION|LOCAL_HERITAGE|NATION_HERITAGE|HERITAGE_LOCAL|HERITAGE_NATION|HERITAGE_HERITAGE)\s+([\d.]+)",
    re.I,
)


def parse_naming_split(s: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Returns:
      name_structure_probs: LL/LH/HL/HH weights (normalized)
      composition_extras: always empty (middle/compound are per-pool in name JSON)

    Accepts both LOCAL_* and NATION_* column tokens (same meaning for name_generation).
    """
    structs: Dict[str, float] = {}
    extras: Dict[str, float] = {}
    for name, wt in _STRUCTURE_RE.findall(s or ""):
        n = name.upper()
        try:
            w = float(wt)
        except ValueError:
            continue
        if n in ("LOCAL_LOCAL", "NATION_NATION"):
            structs["LL"] = structs.get("LL", 0) + w
        elif n in ("LOCAL_HERITAGE", "NATION_HERITAGE"):
            structs["LH"] = structs.get("LH", 0) + w
        elif n in ("HERITAGE_LOCAL", "HERITAGE_NATION"):
            structs["HL"] = structs.get("HL", 0) + w
        elif n == "HERITAGE_HERITAGE":
            structs["HH"] = structs.get("HH", 0) + w
    tot = sum(structs.values()) + sum(extras.values())
    if tot > 0:
        for d in (structs, extras):
            for k in list(d.keys()):
                d[k] = d[k] / tot
    return structs, extras


def composition_has_nationality_code_column(header_line: str) -> bool:
    """
    True if the header row uses the 7-column layout with an explicit NationalityCode column
    (second column). Accepts 'NationalityCode' or 'Nationality_Code'.
    """
    parts = header_line.strip().split("\t")
    if len(parts) < 2:
        return False
    h = parts[1].strip().lower().replace(" ", "_")
    return h in ("nationalitycode", "nationality_code")


def load_composition_rows() -> List[Dict[str, Any]]:
    if not _COMPOSITION_FILE.is_file():
        return []
    text = _COMPOSITION_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 2:
        return []
    pool_map = _build_pool_name_to_code()
    label_to_pool_id = _build_label_to_pool_id()
    pool_id_to_cc = _build_pool_id_to_country_code()
    country_map = _build_country_display_to_code()
    use_nat_code = composition_has_nationality_code_column(lines[0])
    mismatch_warned: set[Tuple[str, str, str]] = set()
    rows: List[Dict[str, Any]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if use_nat_code:
            if len(parts) < 7:
                continue
            region, nat_code_s, country_disp, visual_bucket, pct_s, naming_pool_s, naming_split = (
                parts[:7]
            )
            cc = nat_code_s.strip().upper()
            if len(cc) != 3 or not cc.isalpha():
                continue
            inferred = country_map.get(_norm(country_disp))
            if inferred and inferred != cc and (cc, inferred, country_disp.strip()) not in mismatch_warned:
                mismatch_warned.add((cc, inferred, country_disp.strip()))
                print(
                    f"Warning: composition NationalityCode {cc} != inferred {inferred} "
                    f"for Country {country_disp!r} (using {cc} from file)."
                )
        else:
            if len(parts) < 6:
                continue
            # 6-column: ... naming pool, naming split
            # 7-column: ... naming pool, Persona, naming split (Persona is ignored for parsing)
            if len(parts) >= 7:
                region = parts[0]
                country_disp = parts[1]
                visual_bucket = parts[2]
                pct_s = parts[3]
                naming_pool_s = parts[4]
                naming_split = parts[6]
            else:
                region, country_disp, visual_bucket, pct_s, naming_pool_s, naming_split = parts[:6]
            cc = country_map.get(_norm(country_disp))
            if not cc:
                continue
            cc = cc.upper()
        fed = REGION_TO_FEDERATION.get(region.strip(), region.strip())
        try:
            pct = float(pct_s)
        except ValueError:
            continue
        origin_pool_weights = parse_pool_weights(naming_pool_s, pool_map, label_to_pool_id)
        origin_country_weights = _rollup_pool_weights_to_fifa(origin_pool_weights, pool_id_to_cc)
        struct_probs, extra_probs = parse_naming_split(naming_split)
        rows.append(
            {
                "federation": fed,
                "country_display": country_disp.strip(),
                "nationality_code": cc,
                "visual_bucket": visual_bucket.strip(),
                "percent": pct,
                "origin_pool_weights": origin_pool_weights,
                "origin_country_weights": origin_country_weights,
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


def build_local_core_naming_pools(
    rows: Optional[List[Dict[str, Any]]] = None, *, top_n: int = 6
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Per nationality, weighted sum of origin_pool_weights across composition rows
    (percent/100 * pool weight), keep top_n pools as pool_id for LOCAL sampling.
    """
    if rows is None:
        rows = load_composition_rows()
    by_nat: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        nat = r["nationality_code"]
        pct = float(r["percent"]) / 100.0
        ow = r.get("origin_pool_weights") or r.get("origin_country_weights") or {}
        if not ow:
            ow = {f"country_{nat}": 1.0}
        for pid, w in ow.items():
            pid_norm = pid
            if len(pid) == 3 and pid.isupper():
                pid_norm = f"country_{pid}"
            by_nat[nat][pid_norm] += pct * float(w)

    out: Dict[str, List[Dict[str, Any]]] = {}
    for nat, acc in sorted(by_nat.items()):
        items = sorted(acc.items(), key=lambda x: -x[1])[:top_n]
        tot = sum(w for _, w in items)
        if tot <= 0:
            out[nat] = [{"pool_id": f"country_{nat}", "weight": 1.0}]
            continue
        entries = [{"pool_id": pid, "weight": w / tot} for pid, w in items]
        local_pid = f"country_{nat}"
        # If the dominant pool is this nation's own country_<NAT> pool and clearly majority (>50%), use only that pool.
        if entries and entries[0]["pool_id"] == local_pid and float(entries[0]["weight"]) > 0.5:
            out[nat] = [{"pool_id": local_pid, "weight": 1.0}]
        else:
            out[nat] = entries
    return out


def build_heritage_groups_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """nationality_code -> { group_key -> heritage config }."""
    by_nat: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_nat.setdefault(r["nationality_code"], []).append(r)

    pool_id_to_cc = _build_pool_id_to_country_code()
    heritage: Dict[str, Dict[str, Any]] = {}
    for nat, lst in by_nat.items():
        wsum = sum(x["percent"] for x in lst) or 1.0
        groups: Dict[str, Any] = {}
        for r in lst:
            vb = re.sub(r"[^A-Za-z0-9_]+", "_", r["visual_bucket"]).strip("_")
            gkey = f"{nat}_{vb}"
            rel_pic = f"player_profile_pics/{r['visual_bucket']}"
            ow_pool = r.get("origin_pool_weights")
            if ow_pool is None:
                owc = r.get("origin_country_weights") or {}
                ow_pool = {f"country_{k}": v for k, v in owc.items() if len(k) == 3 and k.isupper()}
            if not ow_pool:
                ow_pool = {f"country_{nat}": 1.0}
            ow_fifa = _rollup_pool_weights_to_fifa(ow_pool, pool_id_to_cc)
            groups[gkey] = {
                "weight": r["percent"] / wsum,
                "picture_folder": rel_pic,
                "origin_pool_weights": ow_pool,
                "origin_country_weights": ow_fifa,
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

    # LOCAL core naming pools:
    # - Treat the existing on-disk `local_core_naming_pools.json` as "frozen" manual data.
    # - Route freshly regenerated results into `local_core_naming_pools_generated.json`.
    # - Only backfill `local_core_naming_pools.json` if it does not exist (or is empty),
    #   so first-time setups still work.
    local_core = build_local_core_naming_pools(rows)
    _write_local_core_naming_pools_json(local_core)

    local_path = _COMPOSITION_DIR / "local_core_naming_pools.json"
    if not local_path.is_file() or local_path.stat().st_size == 0:
        name_data.LOCAL_CORE_NAMING_POOLS.clear()
        name_data.LOCAL_CORE_NAMING_POOLS.update(local_core)

    return n, len(rows)


def _write_local_core_naming_pools_json(local_core: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Write:
      - `data/heritage_composition/local_core_naming_pools_generated.json` (always; regenerated from composition)
      - `data/heritage_composition/local_core_naming_pools.json` (only if missing/empty; never overwrite)
    """
    generated_path = _COMPOSITION_DIR / "local_core_naming_pools_generated.json"
    frozen_path = _COMPOSITION_DIR / "local_core_naming_pools.json"
    text = json.dumps(dict(sorted(local_core.items())), indent=2, ensure_ascii=False) + "\n"

    try:
        generated_path.write_text(text, encoding="utf-8")
    except OSError:
        # Still attempt to backfill frozen file below.
        pass

    try:
        if not frozen_path.is_file() or frozen_path.stat().st_size == 0:
            frozen_path.write_text(text, encoding="utf-8")
    except OSError:
        pass


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
