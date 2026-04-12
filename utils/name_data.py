"""
Name data structures for realistic player name generation.

Loads country-specific name pools (tiered) from data/name_pools/ (country_*.json,
custom_*.json). Optional per-pool fields `middle_name_prob`, `compound_surname_prob`, and
`surname_connector` in each JSON drive name_generation (not the heritage composition split).
Custom pools may set `surname_inherit_pool_id` (e.g. country_XXX) instead of duplicating
`surnames`; resolved after all pools load. The US ethnicity pools (`custom_us_hispanic`,
`custom_us_modern`, `custom_african_american`) use empty `surnames` tiers in JSON and rely on
runtime sampling from `country_USA` (see `effective_surname_pool_for_sampling` in name_generation).

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
from typing import Any, Dict, List, Optional, Set, Tuple

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent
_NAME_POOLS_DIR = _BASE_DIR / "data" / "name_pools"
_COMPOSITION_DIR = _BASE_DIR / "data" / "heritage_composition"
_LOCAL_CORE_FILE = _COMPOSITION_DIR / "local_core_naming_pools.json"
_LEGACY_POOL_FILENAME = re.compile(r"^[A-Z]{3}\.json$")

# ── Name pool tiers (master CSV rank bands; see scripts/import_master_name_pools.py) ──
NAME_POOL_TIER_KEYS: Tuple[str, ...] = (
    "top",
    "very_common",
    "common",
    "familiar",
    "uncommon",
    "rare",
    "very_rare",
)

# Temporary uniform sampling until per-pool `rarity_profile` resolves to weights.
_UNIFORM = 1.0 / len(NAME_POOL_TIER_KEYS)
DEFAULT_GIVEN_NAME_TIER_PROBS: Dict[str, float] = {k: _UNIFORM for k in NAME_POOL_TIER_KEYS}
DEFAULT_SURNAME_TIER_PROBS: Dict[str, float] = {k: _UNIFORM for k in NAME_POOL_TIER_KEYS}

# Legacy 4-tier keys (pre–7-tier pools); flattened then re-bucketed by list position on load.
_LEGACY_TIER_ORDER = ("very_common", "common", "mid", "rare")


def tier_key_for_pool_seq(seq: int) -> str:
    """Map 1-based rank (pool_seq) to tier key."""
    if seq <= 0:
        return "very_rare"
    if seq <= 5:
        return "top"
    if seq <= 15:
        return "very_common"
    if seq <= 30:
        return "common"
    if seq <= 75:
        return "familiar"
    if seq <= 250:
        return "uncommon"
    if seq <= 1000:
        return "rare"
    return "very_rare"


def _normalize_tiered_block(block: Any) -> Dict[str, List[str]]:
    """Ensure all NAME_POOL_TIER_KEYS exist. Legacy 4-tier dicts are re-bucketed by global rank order."""
    if not isinstance(block, dict):
        return {k: [] for k in NAME_POOL_TIER_KEYS}
    keys_present = set(block.keys())
    has_all_seven = all(k in keys_present for k in NAME_POOL_TIER_KEYS)
    if has_all_seven:
        out: Dict[str, List[str]] = {k: [] for k in NAME_POOL_TIER_KEYS}
        for k in NAME_POOL_TIER_KEYS:
            for x in block.get(k) or []:
                if isinstance(x, str) and x.strip():
                    out[k].append(x.strip())
        return out
    # Legacy or mixed: flatten old order, dedupe, assign tier by 1-based index
    flat: List[str] = []
    seen: Set[str] = set()
    for k in _LEGACY_TIER_ORDER:
        for x in block.get(k) or []:
            if not isinstance(x, str):
                continue
            n = x.strip()
            if not n:
                continue
            cf = n.casefold()
            if cf in seen:
                continue
            seen.add(cf)
            flat.append(n)
    out = {k: [] for k in NAME_POOL_TIER_KEYS}
    for i, name in enumerate(flat, start=1):
        out[tier_key_for_pool_seq(i)].append(name)
    return out


def _normalize_tier_probs(data: dict) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Return tier_probs dict with given/surname each summing to 1 over NAME_POOL_TIER_KEYS.
    If missing or wrong shape, use uniform defaults.
    """
    raw = data.get("tier_probs")
    if not isinstance(raw, dict):
        return None
    out: Dict[str, Dict[str, float]] = {}
    for branch in ("given", "surname"):
        p = raw.get(branch)
        if not isinstance(p, dict):
            out[branch] = dict(DEFAULT_GIVEN_NAME_TIER_PROBS if branch == "given" else DEFAULT_SURNAME_TIER_PROBS)
            continue
        if set(p.keys()) == set(NAME_POOL_TIER_KEYS):
            s = sum(float(p[k]) for k in NAME_POOL_TIER_KEYS)
            if s > 0:
                out[branch] = {k: float(p[k]) / s for k in NAME_POOL_TIER_KEYS}
            else:
                out[branch] = dict(
                    DEFAULT_GIVEN_NAME_TIER_PROBS if branch == "given" else DEFAULT_SURNAME_TIER_PROBS
                )
        else:
            out[branch] = dict(
                DEFAULT_GIVEN_NAME_TIER_PROBS if branch == "given" else DEFAULT_SURNAME_TIER_PROBS
            )
    return out


# Deprecated: old pair-based compound bias (7-tier compound uses simplified roll in name_generation).
COMPOUND_SURNAME_TIER_BIAS: Dict[Tuple[str, str], float] = {}

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
        "given_names_male": _normalize_tiered_block(data.get("given_names_male")),
        "surnames": _normalize_tiered_block(copy.deepcopy(ref.get("surnames"))),
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
            "given_names_male": _normalize_tiered_block(data.get("given_names_male")),
            "surnames": _normalize_tiered_block(data.get("surnames")),
        }
        _register_tiered_pool(pool_id, code, tiered, is_custom)
        _register_pool_optional_fields(pool_id, data)
    # Optional: tier probabilities (7-tier; normalized for country pools)
    if "tier_probs" in data and not is_custom:
        tp = _normalize_tier_probs(data)
        if tp is not None:
            COUNTRY_TIER_PROBS[code] = tp


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
