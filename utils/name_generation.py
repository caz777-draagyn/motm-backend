"""
Name generation engine for realistic player names.

Tier-based sampling, heritage LL/LH/HL/HH structure from composition, middle name and
compound surname probabilities from each selected name pool JSON, and anti-duplication.
"""

import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from .name_data import (
    COUNTRY_NAME_POOLS,
    HERITAGE_CONFIG,
    HERITAGE_NAME_POOLS,
    NAME_POOLS_BY_ID,
    NAME_POOL_TIER_KEYS,
    POOL_ID_TO_COUNTRY_CODE,
    compound_surname_prob_for_pool,
    middle_name_prob_for_pool,
    surname_connector_for_pool,
    tier_probs_for_pool,
    DEFAULT_GIVEN_NAME_TIER_PROBS,
    DEFAULT_SURNAME_TIER_PROBS,
)
from .tier_prob_profiles import merge_zero_prob_tiers


@dataclass
class PlayerName:
    """Structured player name with separate components."""
    
    given_first: str
    given_middle: Optional[str] = None
    surname_parts: List[str] = None
    surname_connector: Optional[str] = None
    
    def __post_init__(self):
        if self.surname_parts is None:
            self.surname_parts = []
    
    @property
    def display_full(self) -> str:
        """Full display name: 'John Michael Smith-Jones'"""
        parts = [self.given_first]
        if self.given_middle:
            parts.append(self.given_middle)
        
        if self.surname_parts:
            if len(self.surname_parts) == 2 and self.surname_connector:
                surname = f"{self.surname_parts[0]}{self.surname_connector}{self.surname_parts[1]}"
            else:
                surname = self.surname_parts[0] if self.surname_parts else ""
            parts.append(surname)
        
        return " ".join(parts)
    
    @property
    def display_short(self) -> str:
        """Short display name: 'J. M. Smith-Jones' or 'J. Smith-Jones'"""
        first_initial = self.given_first[0] + "." if self.given_first else ""
        parts = [first_initial]
        
        if self.given_middle:
            parts.append(self.given_middle[0] + ".")
        
        if self.surname_parts:
            if len(self.surname_parts) == 2 and self.surname_connector:
                surname = f"{self.surname_parts[0]}{self.surname_connector}{self.surname_parts[1]}"
            else:
                surname = self.surname_parts[0]
            parts.append(surname)
        
        return " ".join(parts)
    
    def __str__(self) -> str:
        """String representation returns full display name."""
        return self.display_full


def sample_from_tier(
    tier_list: List[str],
    tier_probs: Dict[str, float]
) -> str:
    """
    Sample a name from a tiered list.
    
    Args:
        tier_list: List of names in the selected tier
        tier_probs: Dictionary mapping tier names to probabilities
    
    Returns:
        Random name from the tier
    """
    if not tier_list:
        return ""
    return random.choice(tier_list)


def roll_tier(tier_probs: Dict[str, float]) -> str:
    """
    Roll a tier based on probabilities.
    
    Args:
        tier_probs: Dictionary mapping tier names to probabilities
    
    Returns:
        Selected tier name
    """
    tiers = list(tier_probs.keys())
    weights = [max(0.0, float(tier_probs.get(t, 0.0))) for t in tiers]
    s = sum(weights)
    if s <= 1e-15:
        return tiers[0] if tiers else NAME_POOL_TIER_KEYS[0]
    return random.choices(tiers, weights=weights, k=1)[0]


def roll_tier_with_nonempty(
    tier_probs: Dict[str, float],
    nonempty_tiers: List[str],
) -> str:
    """Prefer tiers that have names when all weights are zero."""
    tiers = list(tier_probs.keys())
    weights = [max(0.0, float(tier_probs.get(t, 0.0))) for t in tiers]
    s = sum(weights)
    if s > 1e-15:
        return random.choices(tiers, weights=weights, k=1)[0]
    pool = [t for t in tiers if t in nonempty_tiers]
    if pool:
        return random.choice(pool)
    return tiers[0] if tiers else NAME_POOL_TIER_KEYS[0]


def sample_name_from_pool(
    name_pool: Dict[str, List[str]],
    tier_probs: Dict[str, float]
) -> str:
    """
    Sample a name from a tiered name pool.
    
    Args:
        name_pool: Dictionary with tier keys and name lists
        tier_probs: Tier probability distribution
    
    Returns:
        Random name sampled from the pool
    """
    eff_pool, eff_probs = merge_zero_prob_tiers(name_pool, tier_probs)
    nonempty = [k for k in NAME_POOL_TIER_KEYS if eff_pool.get(k)]
    tier = roll_tier_with_nonempty(eff_probs, nonempty)
    tier_list = eff_pool.get(tier, [])
    return sample_from_tier(tier_list, eff_probs)


def _names_equivalent(a: str, b: str) -> bool:
    return (a or "").strip().casefold() == (b or "").strip().casefold()


def sample_distinct_from_pool(
    name_pool: Dict[str, List[str]],
    tier_probs: Dict[str, float],
    avoid: str,
    max_attempts: int = 40,
) -> Optional[str]:
    """
    Sample from a tiered pool until we get a name different from `avoid` (case-insensitive).
    If random tries fail, scan tiers for any distinct name. Returns None if the pool has no alternative.
    """
    af = (avoid or "").strip().casefold()
    if not af:
        return sample_name_from_pool(name_pool, tier_probs)
    for _ in range(max_attempts):
        cand = sample_name_from_pool(name_pool, tier_probs)
        if (cand or "").strip() and not _names_equivalent(cand, avoid):
            return cand
    for tier in NAME_POOL_TIER_KEYS:
        for n in name_pool.get(tier, []):
            if (n or "").strip() and not _names_equivalent(n, avoid):
                return n
    return None


def get_country_name_pool(country_code: str, name_type: str) -> Optional[Dict[str, List[str]]]:
    """
    Get name pool for a country and name type.
    
    Args:
        country_code: Country code (e.g., "ENG", "NGA")
        name_type: "given_names_male" or "surnames"
    
    Returns:
        Name pool dictionary or None if not found
    """
    country_pools = COUNTRY_NAME_POOLS.get(country_code)
    if not country_pools:
        return None
    return country_pools.get(name_type)


def get_name_pool(pool_id: str, name_type: str) -> Optional[Dict[str, List[str]]]:
    """
    Tiered names for a pool_id (country_ENG, custom_belgium_dutch) or bare 3-letter FIFA code.
    """
    np = NAME_POOLS_BY_ID.get(pool_id)
    if np:
        return np.get(name_type)
    if len(pool_id) == 3 and pool_id.isupper():
        p = COUNTRY_NAME_POOLS.get(pool_id)
        if p:
            return p.get(name_type)
    return None


def pool_has_names(pool_id: str, name_type: str) -> bool:
    pool = get_name_pool(pool_id, name_type)
    if not pool:
        return False
    return any(len(pool.get(t, [])) > 0 for t in NAME_POOL_TIER_KEYS)


# US custom givens-only pools: empty `surnames` in JSON; sampling uses country_USA surnames at runtime.
US_CUSTOM_POOLS_EMPTY_SURNAME = frozenset(
    {"custom_us_hispanic", "custom_us_modern", "custom_african_american"}
)
_US_SURNAME_FALLBACK_POOL_ID = "country_USA"


def effective_surname_pool_for_sampling(named_pool_id: str) -> Tuple[str, Optional[Dict[str, List[str]]]]:
    """
    Return (pool_id_for_tier_probs, tiered_surname_dict) for RNG.

    Custom US ethnicity pools keep no surname strings on disk; tier_probs / compound / connector
    still come from that pool_id via country_code_for_tier_probs and *_for_pool helpers.
    """
    pool = get_name_pool(named_pool_id, "surnames")
    if pool and pool_has_names(named_pool_id, "surnames"):
        return named_pool_id, pool
    if named_pool_id in US_CUSTOM_POOLS_EMPTY_SURNAME:
        fb = get_name_pool(_US_SURNAME_FALLBACK_POOL_ID, "surnames")
        if fb and pool_has_names(_US_SURNAME_FALLBACK_POOL_ID, "surnames"):
            return _US_SURNAME_FALLBACK_POOL_ID, fb
    return named_pool_id, pool


def _pool_id_is_registered(pool_id: str) -> bool:
    """True if this pool_id was loaded into NAME_POOLS_BY_ID or COUNTRY_NAME_POOLS."""
    if pool_id in NAME_POOLS_BY_ID:
        return True
    return len(pool_id) == 3 and pool_id.isupper() and pool_id in COUNTRY_NAME_POOLS


def _local_pool_entry_is_usable(pool_id: str) -> bool:
    """Local core entry must be loadable and have non-empty given names (and surnames or US fallback)."""
    if not _pool_id_is_registered(pool_id):
        return False
    if not pool_has_names(pool_id, "given_names_male"):
        return False
    if pool_has_names(pool_id, "surnames"):
        return True
    if pool_id in US_CUSTOM_POOLS_EMPTY_SURNAME:
        return pool_has_names(_US_SURNAME_FALLBACK_POOL_ID, "surnames")
    return False


def pool_id_to_country_code(pool_id: str) -> Optional[str]:
    if pool_id.startswith("country_"):
        return pool_id[len("country_") :]
    return None


def country_code_for_tier_probs(pool_id: str, nationality: str) -> str:
    """FIFA-style code for ``tier_probs_for_pool`` fallback when pool JSON has no ``tier_probs``."""
    cc = POOL_ID_TO_COUNTRY_CODE.get(pool_id)
    if cc:
        return cc
    if len(pool_id) == 3 and pool_id.isupper() and pool_id in COUNTRY_NAME_POOLS:
        return pool_id
    if pool_id.startswith("country_"):
        return pool_id[len("country_") :]
    return nationality


def resolve_local_pool_id(nationality: str) -> str:
    """
    pool_id to use for LOCAL given/surname (local_core_naming_pools.json or country_<NAT>).
    """
    from .name_data import LOCAL_CORE_NAMING_POOLS

    entries = LOCAL_CORE_NAMING_POOLS.get(nationality)
    if not entries:
        cand = f"country_{nationality}"
        if cand in NAME_POOLS_BY_ID:
            return cand
        if nationality in COUNTRY_NAME_POOLS:
            return nationality
        return cand if cand in NAME_POOLS_BY_ID else nationality
    # Only choose among entries that are actually loaded and have both given + surnames.
    # Otherwise random.choices can pick a missing pool and fall through to bare FIFA code
    # (e.g. ATG) with no name data, while heritage still uses country_JAM/TTO — breaks LH/LL.
    valid: List[Tuple[str, float]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        pid = str(e.get("pool_id") or "").strip()
        if not pid:
            continue
        w = float(e.get("weight", 1.0))
        if _local_pool_entry_is_usable(pid):
            valid.append((pid, w))
    if valid:
        pool_ids = [p for p, _ in valid]
        weights = [w for _, w in valid]
        return random.choices(pool_ids, weights=weights, k=1)[0]
    cand = f"country_{nationality}"
    if cand in NAME_POOLS_BY_ID and _local_pool_entry_is_usable(cand):
        return cand
    if nationality in COUNTRY_NAME_POOLS and _local_pool_entry_is_usable(nationality):
        return nationality
    return cand if cand in NAME_POOLS_BY_ID else nationality


def resolve_local_pool_country(nationality: str) -> str:
    """FIFA code for tier probabilities for the resolved local pool_id."""
    return country_code_for_tier_probs(resolve_local_pool_id(nationality), nationality)


def heritage_origin_weights_as_pool_ids(heritage_config: dict) -> Dict[str, float]:
    """Normalize origin_pool_weights or legacy origin_country_weights (FIFA keys) to pool_id keys."""
    ow = heritage_config.get("origin_pool_weights")
    if ow:
        return dict(ow)
    ow = heritage_config.get("origin_country_weights") or {}
    if not ow:
        return {}
    out: Dict[str, float] = {}
    for k, v in ow.items():
        if len(k) == 3 and k.isupper():
            out[f"country_{k}"] = float(v)
        else:
            out[k] = float(v)
    return out


def _coerce_origin_pool_id(origin: Optional[str]) -> Optional[str]:
    if not origin:
        return None
    if origin.startswith("country_") or origin.startswith("custom_"):
        return origin
    if len(origin) == 3 and origin.isupper():
        return f"country_{origin}"
    return origin


def select_heritage_group(nationality: str) -> Optional[str]:
    """
    Select a heritage group for a player based on nationality.
    
    Args:
        nationality: Player's nationality code
    
    Returns:
        Heritage group name or None if no heritage groups defined
    """
    heritage_groups = HERITAGE_CONFIG.get(nationality)
    if not heritage_groups:
        return None
    
    # Filter out groups with zero or negative weights
    groups = []
    weights = []
    for group_name, group_config in heritage_groups.items():
        weight = group_config.get("weight", 0.0)
        if weight > 0:
            groups.append(group_name)
            weights.append(weight)
    
    if not groups:
        return None
    
    return random.choices(groups, weights=weights, k=1)[0]


def select_origin_pool_id(nationality: str, heritage_group: str) -> Optional[str]:
    """
    Select origin naming pool_id (country_* or custom_*) for heritage name generation.
    Falls back to highest-weight pool that has non-empty given names.
    """
    heritage_config = HERITAGE_CONFIG.get(nationality, {}).get(heritage_group)
    if not heritage_config:
        return None

    origin_weights = heritage_origin_weights_as_pool_ids(heritage_config)
    if not origin_weights:
        return None

    pool_ids = list(origin_weights.keys())
    weights = [origin_weights[p] for p in pool_ids]
    selected = random.choices(pool_ids, weights=weights, k=1)[0]

    if pool_has_names(selected, "given_names_male"):
        return selected
    sorted_pools = sorted(origin_weights.items(), key=lambda x: x[1], reverse=True)
    for pid, _ in sorted_pools:
        if pool_has_names(pid, "given_names_male"):
            return pid
    return sorted_pools[0][0] if sorted_pools else selected


def select_origin_country(nationality: str, heritage_group: str) -> Optional[str]:
    """Backward compatibility: returns FIFA code for the selected origin pool."""
    pid = select_origin_pool_id(nationality, heritage_group)
    if not pid:
        return None
    return country_code_for_tier_probs(pid, nationality)


def select_name_structure(nationality: str, heritage_group: str) -> Tuple[str, str]:
    """
    Select name structure pair (given origin, surname origin).
    
    Returns:
        Tuple of (given_origin, surname_origin) where each is "LOCAL" or "HERITAGE"
    """
    heritage_config = HERITAGE_CONFIG.get(nationality, {}).get(heritage_group)
    if not heritage_config:
        return ("LOCAL", "LOCAL")
    
    structure_probs = heritage_config.get("name_structure_probs", {})
    if not structure_probs:
        return ("LOCAL", "LOCAL")
    
    # Map structure codes to (given, surname) origins
    structure_map = {
        "LL": ("LOCAL", "LOCAL"),
        "LH": ("LOCAL", "HERITAGE"),
        "HL": ("HERITAGE", "LOCAL"),
        "HH": ("HERITAGE", "HERITAGE")
    }
    
    structures = list(structure_probs.keys())
    weights = [structure_probs[s] for s in structures]
    selected = random.choices(structures, weights=weights, k=1)[0]
    
    return structure_map.get(selected, ("LOCAL", "LOCAL"))


def select_name_structure_with_variants(
    nationality: str, heritage_group: str
) -> Tuple[str, str, None]:
    """
    Returns (given_origin, surname_origin, None). Middle and compound surname are rolled
    per name pool JSON after pools are chosen, not from composition extras.
    """
    g, s = select_name_structure(nationality, heritage_group)
    return (g, s, None)


def name_structure_code(given_origin: str, surname_origin: str) -> str:
    """LL/LH/HL/HH from LOCAL/HERITAGE origins (matches rolled structure in generate_name)."""
    return {
        ("LOCAL", "LOCAL"): "LL",
        ("LOCAL", "HERITAGE"): "LH",
        ("HERITAGE", "LOCAL"): "HL",
        ("HERITAGE", "HERITAGE"): "HH",
    }.get((given_origin, surname_origin), "LL")


def generate_name(
    nationality: str,
    heritage_group: Optional[str] = None,
    origin_country: Optional[str] = None,
    used_names: Optional[Set[str]] = None,
    max_retries: int = 50,
    name_pool_debug: Optional[Dict[str, str]] = None,
) -> PlayerName:
    """
    Generate a player name based on nationality and heritage.
    
    Args:
        nationality: Player's nationality code
        heritage_group: Optional heritage group (if None, will be selected)
        origin_country: Optional origin country (if None and heritage, will be selected)
        used_names: Set of already-used full names to avoid duplicates
        max_retries: Maximum retries if duplicate detected
        name_pool_debug: If provided, cleared each attempt then filled with pool ids used for sampling
    
    Returns:
        PlayerName object with structured name components
    """
    if used_names is None:
        used_names = set()

    name = PlayerName(given_first="NoFirstName", surname_parts=["NoLastName"])
    origin_override = _coerce_origin_pool_id(origin_country)
    for attempt in range(max_retries):
        if name_pool_debug is not None:
            name_pool_debug.clear()
        local_pool_id = resolve_local_pool_id(nationality)
        # Select heritage group if not provided
        if heritage_group is None:
            heritage_group = select_heritage_group(nationality)
        
        # Determine name structure
        if heritage_group and heritage_group != "ENG_Mainstream":
            origin_pool_id = origin_override
            if origin_pool_id is None:
                origin_pool_id = select_origin_pool_id(nationality, heritage_group)

            if origin_pool_id and not pool_has_names(origin_pool_id, "given_names_male"):
                heritage_config = HERITAGE_CONFIG.get(nationality, {}).get(heritage_group)
                if heritage_config:
                    origin_weights = heritage_origin_weights_as_pool_ids(heritage_config)
                    if origin_weights:
                        for pid, _ in sorted(
                            origin_weights.items(), key=lambda x: x[1], reverse=True
                        ):
                            if pool_has_names(pid, "given_names_male"):
                                origin_pool_id = pid
                                break

            given_origin, surname_origin, _ = select_name_structure_with_variants(
                nationality, heritage_group
            )
        else:
            given_origin = "LOCAL"
            surname_origin = "LOCAL"
            origin_pool_id = None
        
        # If heritage origin missing, fall back to local pool_id for HERITAGE parts
        eff_heritage_pid = (
            origin_pool_id if origin_pool_id is not None else local_pool_id
        )
        given_pid = eff_heritage_pid if given_origin == "HERITAGE" else local_pool_id
        surname_pid = eff_heritage_pid if surname_origin == "HERITAGE" else local_pool_id

        if name_pool_debug is not None:
            name_pool_debug["local_pool_id"] = local_pool_id
            name_pool_debug["given_pool_id"] = given_pid
            name_pool_debug["surname_pool_id"] = surname_pid
            name_pool_debug["name_structure"] = name_structure_code(
                given_origin, surname_origin
            )
            if origin_pool_id is not None:
                name_pool_debug["heritage_origin_pool_id"] = str(origin_pool_id)
        
        given_pool = get_name_pool(given_pid, "given_names_male")
        if not given_pool:
            given_pool = get_name_pool(local_pool_id, "given_names_male")
        if not given_pool:
            given_pool = get_name_pool(eff_heritage_pid, "given_names_male")

        surname_sample_id, surname_pool = effective_surname_pool_for_sampling(surname_pid)
        if not surname_pool or not pool_has_names(surname_sample_id, "surnames"):
            surname_sample_id, surname_pool = effective_surname_pool_for_sampling(local_pool_id)
        if not surname_pool or not pool_has_names(surname_sample_id, "surnames"):
            surname_sample_id, surname_pool = effective_surname_pool_for_sampling(eff_heritage_pid)

        if not given_pool or not surname_pool or not pool_has_names(surname_sample_id, "surnames"):
            name = PlayerName(
                given_first="NoFirstName",
                surname_parts=["NoLastName"],
            )
            full_name = name.display_full
            if full_name not in used_names:
                used_names.add(full_name)
                return name
            continue

        if name_pool_debug is not None and surname_sample_id != surname_pid:
            name_pool_debug["surname_sampled_from_pool_id"] = surname_sample_id

        g_cc = country_code_for_tier_probs(given_pid, nationality)
        s_cc = country_code_for_tier_probs(surname_sample_id, nationality)
        given_tier_probs = tier_probs_for_pool(given_pid, g_cc, "given")
        surname_tier_probs = tier_probs_for_pool(surname_sample_id, s_cc, "surname")
        
        # Sample given name
        given_first = sample_name_from_pool(given_pool, given_tier_probs)
        if not (given_first or "").strip():
            given_first = "NoFirstName"
        
        # Sample surname
        surname_first = sample_name_from_pool(surname_pool, surname_tier_probs)
        if not (surname_first or "").strip():
            surname_first = "NoLastName"
        surname_parts = [surname_first]
        surname_connector = None

        # Compound surname: probability from the *surname* pool JSON only
        compound_prob = compound_surname_prob_for_pool(surname_pid, nationality)
        # Second compound part: same tier weights as primary surname draw (temporary uniform / profile).
        compound_tier_probs = dict(surname_tier_probs)
        if random.random() < compound_prob:
            surname_second = sample_name_from_pool(surname_pool, compound_tier_probs)
            if not (surname_second or "").strip():
                surname_second = "NoLastName"
            if _names_equivalent(surname_second, surname_first):
                alt = sample_distinct_from_pool(
                    surname_pool, compound_tier_probs, surname_first
                )
                surname_second = alt if alt else None
            if surname_second is not None and (surname_second or "").strip():
                surname_parts.append(surname_second)
                surname_connector = surname_connector_for_pool(surname_pid, nationality)

        # Middle name: probability from the *given* pool JSON; sample from same given pool
        middle_name = None
        middle_prob = middle_name_prob_for_pool(given_pid, nationality)
        if random.random() < middle_prob and given_pool:
            middle_tier_probs = tier_probs_for_pool(given_pid, g_cc, "given")
            middle_name = sample_name_from_pool(given_pool, middle_tier_probs)
            if middle_name and _names_equivalent(middle_name, given_first):
                middle_name = sample_distinct_from_pool(
                    given_pool, middle_tier_probs, given_first
                )

        # Max three logical parts: not given + middle + two surnames — drop middle or second surname
        if middle_name and len(surname_parts) == 2:
            if random.random() < 0.5:
                middle_name = None
            else:
                surname_parts = [surname_parts[0]]
                surname_connector = None
        
        # Create name object
        name = PlayerName(
            given_first=given_first,
            given_middle=middle_name,
            surname_parts=surname_parts,
            surname_connector=surname_connector
        )
        
        # Check for duplicates
        full_name = name.display_full
        if full_name not in used_names:
            used_names.add(full_name)
            return name
    
    # If max retries exceeded, return the last generated name anyway
    return name


def generate_name_string(nationality: str, **kwargs) -> str:
    """
    Convenience function to generate a name and return as string.
    
    Args:
        nationality: Player's nationality code
        **kwargs: Additional arguments passed to generate_name()
    
    Returns:
        Full display name as string
    """
    name = generate_name(nationality, **kwargs)
    return name.display_full
