"""
Name data structures for realistic player name generation.

Loads country-specific name pools (tiered) from data/name_pools/ (country_*.json,
custom_*.json). Optional per-pool fields `middle_name_prob`, `compound_surname_prob`, and
`surname_connector` in each JSON drive name_generation (not the heritage composition split).
Custom pools may set `surname_inherit_pool_id` (e.g. country_USA) instead of duplicating
`surnames`; resolved after all pools load.

Heritage, federation, and optional JSON mirrors come from
data/heritage_composition/FullHeritageAndNamingComposition.txt at import
(heritage_composition.apply_to_name_data): HERITAGE_CONFIG, COUNTRY_FEDERATION,
LOCAL_CORE_NAMING_POOLS, HERITAGE_PICTURE_FOLDER_MAP.

The composition file is tab-separated; preferred columns are:
Region, NationalityCode (FIFA 3-letter), Country (display name), VisualBucket, percent,
naming pool, naming split. See utils/heritage_composition.py module docstring.

To support manual edits of `data/heritage_composition/local_core_naming_pools.json`, the app
loads that frozen file first, and regenerated results are routed into
`data/heritage_composition/local_core_naming_pools_generated.json` instead of overwriting the
frozen file.

Optional: heritage_groups_export.json from scripts/migrate_naming_and_heritage_exports.py (review only).
"""

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent
_NAME_POOLS_DIR = _BASE_DIR / "data" / "name_pools"
_COMPOSITION_DIR = _BASE_DIR / "data" / "heritage_composition"
_LOCAL_CORE_FILE = _COMPOSITION_DIR / "local_core_naming_pools.json"
_LEGACY_POOL_FILENAME = re.compile(r"^[A-Z]{3}\.json$")

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_GIVEN_NAME_TIER_PROBS = {
    "very_common": 0.55,
    "common": 0.30,
    "mid": 0.13,
    "rare": 0.02
}

DEFAULT_SURNAME_TIER_PROBS = {
    "very_common": 0.45,
    "common": 0.35,
    "mid": 0.17,
    "rare": 0.03
}

# Compound surname tier bias (for surname2)
# 70% common/common, 25% common/mid, 5% mid/mid, ~0-2% rare involvement
COMPOUND_SURNAME_TIER_BIAS = {
    ("common", "common"): 0.70,
    ("common", "mid"): 0.25,
    ("mid", "mid"): 0.05,
    ("very_common", "common"): 0.00,
    ("common", "rare"): 0.00,
    ("mid", "rare"): 0.00,
    ("rare", "rare"): 0.00
}

# ── Load name pools from JSON ─────────────────────────────────────────────────
# Primary key: FIFA-style country code (e.g. ENG). Also indexed by pool_id in NAME_POOLS_BY_ID.
COUNTRY_NAME_POOLS: Dict[str, Dict] = {}
NAME_POOLS_BY_ID: Dict[str, Dict] = {}
# pool_id (country_* / custom_*) -> FIFA code from JSON (tier probs / connectors)
POOL_ID_TO_COUNTRY_CODE: Dict[str, str] = {}
COUNTRY_TIER_PROBS: Dict[str, Dict[str, Dict[str, float]]] = {}
MIDDLE_NAME_PROBS: Dict[str, float] = {"default": 0.15}
COMPOUND_SURNAME_PROBS: Dict[str, float] = {"default": 0.05}
SURNAME_CONNECTORS: Dict[str, str] = {"default": "-"}
# Per pool_id (country_* / custom_*): optional fields from each JSON; used by name_generation.
POOL_MIDDLE_NAME_PROBS: Dict[str, float] = {}
POOL_COMPOUND_SURNAME_PROBS: Dict[str, float] = {}
POOL_SURNAME_CONNECTORS: Dict[str, str] = {}

# nationality_code -> [{ "pool_id": "country_XXX", "weight": float }, ...]
LOCAL_CORE_NAMING_POOLS: Dict[str, List[Dict[str, Any]]] = {}

# Remap legacy / removed pool_id strings from local_core_naming_pools.json to pools that exist on disk.
_LOCAL_CORE_POOL_ID_ALIASES: Dict[str, str] = {
    "custom_wales": "country_WAL",
    "custom_scotland": "country_SCO",
    "custom_northern_ireland": "country_NIR",
    "custom_cambodia": "country_CAM",
    "custom_china_north": "country_CHN",
    "custom_china_south": "country_CHN",
    "custom_congo": "country_CGO",
    "custom_israel_hebrew": "country_ISR",
    "custom_malaysia_indian": "custom_malaysia_chinese",
    "custom_new_caledonia": "country_NCL",
    "custom_samoa": "country_SAM",
    "custom_solomon_islands": "country_SOL",
    "custom_suriname": "country_SUR",
    "custom_tajikistan": "country_TJK",
    "custom_tonga": "country_TGA",
    "custom_uae": "country_UAE",
    "custom_vanuatu": "country_VAN",
    # Indian Singapore names: no standalone country_SIN pool (use regional Indian pool)
    "custom_singapore_indian": "custom_india_gangetic",
    "country_GLP": "country_FRA",
}


def _alias_local_core_pool_id(pool_id: str) -> str:
    return _LOCAL_CORE_POOL_ID_ALIASES.get(pool_id, pool_id)


def _register_pool_optional_fields(pool_id: str, data: dict) -> None:
    """Middle / compound / connector from pool JSON, keyed by pool_id; also mirror country_* into legacy dicts."""
    code = data.get("country_code")
    is_custom = pool_id.startswith("custom_")
    if "middle_name_prob" in data:
        POOL_MIDDLE_NAME_PROBS[pool_id] = float(data["middle_name_prob"])
        if code and not is_custom:
            MIDDLE_NAME_PROBS[str(code)] = data["middle_name_prob"]
    if "compound_surname_prob" in data:
        POOL_COMPOUND_SURNAME_PROBS[pool_id] = float(data["compound_surname_prob"])
        if code and not is_custom:
            COMPOUND_SURNAME_PROBS[str(code)] = data["compound_surname_prob"]
    if "surname_connector" in data:
        POOL_SURNAME_CONNECTORS[pool_id] = str(data["surname_connector"])
        if code and not is_custom:
            SURNAME_CONNECTORS[str(code)] = data["surname_connector"]


def middle_name_prob_for_pool(pool_id: str, nationality: str) -> float:
    v = POOL_MIDDLE_NAME_PROBS.get(pool_id)
    if v is not None:
        return float(v)
    cc = POOL_ID_TO_COUNTRY_CODE.get(pool_id, nationality)
    return float(MIDDLE_NAME_PROBS.get(cc, MIDDLE_NAME_PROBS.get("default", 0.15)))


def compound_surname_prob_for_pool(pool_id: str, nationality: str) -> float:
    v = POOL_COMPOUND_SURNAME_PROBS.get(pool_id)
    if v is not None:
        return float(v)
    cc = POOL_ID_TO_COUNTRY_CODE.get(pool_id, nationality)
    return float(COMPOUND_SURNAME_PROBS.get(cc, COMPOUND_SURNAME_PROBS.get("default", 0.05)))


def surname_connector_for_pool(pool_id: str, nationality: str) -> str:
    v = POOL_SURNAME_CONNECTORS.get(pool_id)
    if v is not None:
        return str(v)
    cc = POOL_ID_TO_COUNTRY_CODE.get(pool_id, nationality)
    return str(SURNAME_CONNECTORS.get(cc, SURNAME_CONNECTORS.get("default", "-")))


def _register_tiered_pool(pool_id: str, code: str, tiered: Dict[str, Any], is_custom: bool) -> None:
    NAME_POOLS_BY_ID[pool_id] = tiered
    POOL_ID_TO_COUNTRY_CODE[pool_id] = code
    if not is_custom:
        COUNTRY_NAME_POOLS[code] = tiered


def _ingest_surname_inherit_pool(data: dict) -> None:
    """Finish loading a pool that lists `surname_inherit_pool_id` instead of inline `surnames`."""
    code = data.get("country_code")
    if not code:
        return
    pool_id = data.get("pool_id") or f"country_{code}"
    ref_id = (data.get("surname_inherit_pool_id") or "").strip()
    if not ref_id:
        return
    ref = NAME_POOLS_BY_ID.get(ref_id)
    if not ref or not ref.get("surnames"):
        print(
            f"Warning: surname_inherit_pool_id {ref_id!r} missing or has no surnames "
            f"(pool {pool_id})"
        )
        return
    tiered = {
        "given_names_male": data["given_names_male"],
        "surnames": copy.deepcopy(ref["surnames"]),
    }
    is_custom = pool_id.startswith("custom_")
    _register_tiered_pool(pool_id, code, tiered, is_custom)
    _register_pool_optional_fields(pool_id, data)


def _ingest_name_pool_file(json_file: Path, data: dict) -> None:
    code = data.get("country_code")
    if not code:
        print(f"Warning: No country_code in {json_file}, skipping")
        return
    pool_id = data.get("pool_id") or f"country_{code}"
    is_custom = pool_id.startswith("custom_")
    # Name pools (required): given + surnames, or given + surname_inherit_pool_id (resolved after load)
    inherit = (data.get("surname_inherit_pool_id") or "").strip()
    if inherit and "given_names_male" in data and "surnames" not in data:
        return
    if "given_names_male" in data and "surnames" in data:
        tiered = {
            "given_names_male": data["given_names_male"],
            "surnames": data["surnames"],
        }
        _register_tiered_pool(pool_id, code, tiered, is_custom)
        _register_pool_optional_fields(pool_id, data)
    # Optional: tier probabilities
    if "tier_probs" in data and not is_custom:
        COUNTRY_TIER_PROBS[code] = data["tier_probs"]


def _load_name_pools():
    """Load name pools: country_*.json, custom_*.json, legacy <CCC>.json."""
    if not _NAME_POOLS_DIR.exists():
        return

    seen: set[Path] = set()
    globs: List[Path] = []
    for pattern in ("country_*.json", "custom_*.json"):
        for fp in sorted(_NAME_POOLS_DIR.glob(pattern)):
            if fp not in seen:
                seen.add(fp)
                globs.append(fp)
    for fp in sorted(_NAME_POOLS_DIR.glob("*.json")):
        if fp in seen:
            continue
        if _LEGACY_POOL_FILENAME.match(fp.name):
            globs.append(fp)

    for json_file in globs:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load name pool {json_file}: {e}")
            continue
        _ingest_name_pool_file(json_file, data)

    for json_file in globs:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue
        if (data.get("surname_inherit_pool_id") or "").strip() and "surnames" not in data:
            _ingest_surname_inherit_pool(data)


def _load_local_core_naming_pools() -> None:
    if not _LOCAL_CORE_FILE.is_file():
        return
    try:
        raw = json.loads(_LOCAL_CORE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not load local core naming pools: {e}")
        return
    if not isinstance(raw, dict):
        return
    for nat, entries in raw.items():
        if not isinstance(entries, list) or not entries:
            continue
        fixed: List[Dict[str, Any]] = []
        for e in entries:
            if isinstance(e, dict) and e.get("pool_id"):
                ne = dict(e)
                pid = str(ne["pool_id"])
                aliased = _alias_local_core_pool_id(pid)
                if aliased != pid:
                    ne["pool_id"] = aliased
                fixed.append(ne)
            else:
                fixed.append(e)
        LOCAL_CORE_NAMING_POOLS[str(nat)] = fixed


# ── Heritage (filled only from FullHeritageAndNamingComposition.txt) ───────────
HERITAGE_CONFIG: Dict[str, Dict] = {}
HERITAGE_PICTURE_FOLDER_MAP: Dict[str, str] = {}

# Legacy alias — some code references this; it's now a subset of COUNTRY_NAME_POOLS
HERITAGE_NAME_POOLS: Dict[str, Dict] = {}

# Country code -> confederation (UEFA, CONMEBOL, …) from heritage composition
COUNTRY_FEDERATION: Dict[str, str] = {}


# ── Initialize on import ──────────────────────────────────────────────────────
_load_name_pools()


def _apply_heritage_composition_file():
    """Load FullHeritageAndNamingComposition.txt into heritage + local core; fallback JSON if empty."""
    try:
        from utils import heritage_composition

        # Load LOCAL core pools from the (potentially manually edited) frozen JSON first.
        # `heritage_composition.apply_to_name_data()` will only backfill it if missing/empty.
        _load_local_core_naming_pools()

        n, _rows = heritage_composition.apply_to_name_data()
        if n == 0:
            # If the composition overlay isn't available, just keep whatever we loaded from disk.
            _load_local_core_naming_pools()
    except Exception as e:
        print(f"Warning: heritage composition overlay skipped: {e}")
        _load_local_core_naming_pools()


_apply_heritage_composition_file()

# Build HERITAGE_NAME_POOLS for backward compatibility
# Any country referenced in heritage groups but not a "main" nationality gets added here
def _fifa_from_origin_pool_id(pool_id: str) -> Optional[str]:
    cc = POOL_ID_TO_COUNTRY_CODE.get(pool_id)
    if cc:
        return cc
    if pool_id.startswith("country_") and len(pool_id) > len("country_"):
        return pool_id[len("country_") :]
    return None


for _nat_code, _groups in HERITAGE_CONFIG.items():
    for _group_name, _group_config in _groups.items():
        _pool_w = _group_config.get("origin_pool_weights") or {}
        _fifa_keys: Set[str] = set()
        for _pid in _pool_w.keys():
            _f = _fifa_from_origin_pool_id(_pid)
            if _f:
                _fifa_keys.add(_f)
        for _origin_code in _group_config.get("origin_country_weights", {}).keys():
            if len(_origin_code) == 3 and _origin_code.isupper():
                _fifa_keys.add(_origin_code)
        for _origin_code in _fifa_keys:
            if _origin_code in COUNTRY_NAME_POOLS and _origin_code != _nat_code:
                HERITAGE_NAME_POOLS[_origin_code] = COUNTRY_NAME_POOLS[_origin_code]
