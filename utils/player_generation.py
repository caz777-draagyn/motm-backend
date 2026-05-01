"""
Player generation module: Creates new players with initial attributes and development parameters.
Based on the PlayerGenAndTraining notebook.
"""

import random
import math
import uuid
from typing import Dict, Optional, Tuple, List, Set
import numpy as np

from match_engine.constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS
from .name_generation import generate_name_string

# Non-playing attributes (personality/mental traits)
NON_PLAYING_ATTRIBUTES = ["Injury Proneness", "Professionalism", "Adaptability", "Aggression"]

# Position traits (role specialization)
POSITION_TRAITS = [
    "Natural Winger", "Deep-Lying Playmaker", "Box-to-Box",
    "Ball-Playing Defender", "Poacher", "Target Forward",
    "Wing Back", "Sweeper Keeper"
]

# Gainable traits (can be developed/acquired)
GAINABLE_TRAITS = [
    "Flair", "Leader", "Big-Game Player", "Workhorse",
    "Set-Piece Specialist", "Tireless Runner", "Speedster",
    "Poacher", "Target Man", "Playmaker"
]

# Nationality codes
NATIONALITIES = ["ENG", "SCO", "WAL", "NIR", "IRL", "ESP", "FRA", "GER", "BRA", "ARG", "NED", "ITA"]
SKIN_TONES = ["Light", "Tan", "Brown", "Dark"]


def clamp(v: int, lo: int = 1, hi: int = 20) -> int:
    """Clamp value between lo and hi."""
    return max(lo, min(hi, v))


def _format_naming_pool_attempted(d: Dict[str, str]) -> Optional[str]:
    """Human-readable line for workbench: which pools were used for name sampling."""
    if not d:
        return None
    order_keys = (
        "mode",
        "name_structure",
        "local_pool_id",
        "heritage_pool_id",
        "heritage_origin_pool_id",
        "given_pool_id",
        "surname_pool_id",
        "given_sample_pool_id",
        "surname_sample_pool_id",
    )
    seen: Set[str] = set()
    parts: List[str] = []
    for k in order_keys:
        if k in d:
            parts.append(f"{k}={d[k]}")
            seen.add(k)
    for k in sorted(d.keys()):
        if k not in seen:
            parts.append(f"{k}={d[k]}")
    return " | ".join(parts)


def rnd_name(
    nationality: Optional[str] = None,
    used_names: Optional[set] = None,
    name_pool_debug: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate a random player name using the new name generation system.
    
    Args:
        nationality: Player's nationality code (defaults to "ENG" if not provided)
        used_names: Set of already-used names to avoid duplicates
    
    Returns:
        Full display name as string
    """
    if nationality is None:
        nationality = "ENG"  # Default to England
    
    return generate_name_string(nationality, used_names=used_names, name_pool_debug=name_pool_debug)


def sample_potential(
    youth_facilities: int,
    is_goalkeeper: bool,
    *,
    alpha_base: float = 2.0,
    beta_base: float = 2.5,
    beta_facility_scale: float = 20.0,
    tail_gamma: float = 1.0,
) -> int:
    """
    Skewed potential distribution: high values rare.
    Youth facilities directly influence Beta distribution parameters.
    GK potential scaled down.
    """
    # Youth facility influence — better facilities reduce beta (less skew to low)
    alpha = float(alpha_base)
    beta = float(beta_base) + (10 - youth_facilities) / float(beta_facility_scale)

    # Sample from adjusted Beta distribution
    raw_score = float(np.random.beta(alpha, beta))

    # Optional post-transform to tweak the extreme tail (gamma > 1 makes top end rarer)
    if tail_gamma and float(tail_gamma) != 1.0:
        g = max(0.01, float(tail_gamma))
        raw_score = raw_score ** g

    # Scale for GK vs outfield
    max_points = 3000 if not is_goalkeeper else int(3000 * len(GOALKEEPER_ATTRS) / len(OUTFIELD_ATTRS))

    return clamp(int(raw_score * max_points), 200, max_points)


def apply_birth_development(
    is_gk: bool,
    potential: int,
    birth_dev_pct: float,
    DP_PER_ATTR_POINT: float = 10.0,
) -> Tuple[Dict[str, int], float, float]:
    """
    Returns: (attributes dict, nominal_dp_total, assigned_dp_total)

    - Start all attributes at 1.
    - Birth budget = potential * birth_dev_pct - (num_attrs * 5).
      (Charges 5 DP per attribute to represent the skill floor at 1.)
    - Spend remaining budget in random chunks [0.1..15] with band efficiencies:
        1–5   : 50% chance -> double assigned
        6–15  : assigned = nominal
        16–17 : 50% chance lose
        18–19 : 75% chance lose
        20    : reroll without consuming nominal
    - Convert assigned DP to +1 attribute when carry >= DP_PER_ATTR_POINT, cap 20.
    """
    attrs_list = GOALKEEPER_ATTRS if is_gk else OUTFIELD_ATTRS
    attrs = {a: 1 for a in attrs_list}
    carry = {a: 0.0 for a in attrs_list}

    # --- Baseline cost for starting at 1 in every attribute ---
    base_cost = len(attrs_list) * 5.0
    raw_budget = float(potential) * float(birth_dev_pct)
    budget = max(0.0, raw_budget - base_cost)

    nominal_total = 0.0   # DP attempted (sum of chunks that count nominally)
    assigned_total = 0.0  # DP actually assigned after efficiency rules

    def all_capped():
        return all(v >= 20 for v in attrs.values())

    while budget - nominal_total >= 0.1 - 1e-12:
        if all_capped():
            break

        # pick a non-20 attribute
        for _ in range(50):
            a = random.choice(attrs_list)
            if attrs[a] < 20:
                break
        else:
            break

        val = attrs[a]
        if val >= 20:
            continue

        # Random DP chunk in [1, 15]
        chunk = round(random.uniform(1, 15), 3)

        # Efficiency rules -> assigned DP (and consume nominal accordingly)
        assigned = 0.0
        if 1 <= val <= 4:
            assigned = chunk * (2 if random.random() < 0.5 else 1)
            nominal_total += chunk
        elif 5 <= val <= 14:
            assigned = chunk
            nominal_total += chunk
        elif 15 <= val <= 17:
            assigned = chunk if random.random() < 0.5 else 0.0
            nominal_total += chunk
        elif 18 <= val <= 19:
            assigned = chunk if random.random() < 0.33 else 0.0
            nominal_total += chunk

        assigned_total += assigned

        # Convert assigned DP to attribute points via carry
        if assigned > 0 and attrs[a] < 20:
            carry[a] += assigned
            while carry[a] >= DP_PER_ATTR_POINT and attrs[a] < 20:
                attrs[a] += 1
                carry[a] -= DP_PER_ATTR_POINT

    return attrs, round(nominal_total, 3), round(assigned_total, 3)


def create_player_data(
    *,
    club_id: Optional[str],
    youth_facilities: int,
    is_goalkeeper: bool = False,
    youth_player: bool = False,
    nationality: Optional[str] = None,
    heritage_options: Optional[List[str]] = None,
    potential_alpha_base: float = 2.0,
    potential_beta_base: float = 2.5,
    potential_beta_facility_scale: float = 20.0,
    potential_tail_gamma: float = 1.0,
) -> Dict:
    """
    Create player data dictionary with all generation parameters.
    This can be used to populate a Player model instance.
    
    Returns a dict with all player fields for database insertion.
    """
    # Actual starting age based on youth flag
    if youth_player:
        start_age_years, start_age_months = 15, 0
    else:
        start_age_years, start_age_months = 16, 0

    actual_age_months = start_age_years * 12 + start_age_months
    baseline_16m = 16 * 12
    training_age_weeks = max(0, actual_age_months - baseline_16m)

    # Potential
    potential = sample_potential(
        youth_facilities,
        is_goalkeeper,
        alpha_base=potential_alpha_base,
        beta_base=potential_beta_base,
        beta_facility_scale=potential_beta_facility_scale,
        tail_gamma=potential_tail_gamma,
    )

    # Dev splits
    birth_dev_pct = round(random.uniform(0.20, 0.40), 2)
    base_training_pct = round(random.uniform(0.10, 0.40), 2)
    growth_training_pct = round(max(0.0, 1.0 - birth_dev_pct - base_training_pct), 2)

    # ---- Weighted growth_peak_age (b parameter: 1.0 to 10.0, steps 0.5) ----
    # Decreasing probability for higher values, ~10% should have b > 8
    b_values = [1.0 + i * 0.5 for i in range(19)]  # 1.0, 1.5, 2.0, ..., 10.0
    b_weights = []
    for b_val in b_values:
        # Exponential decay: weight decreases as b increases
        # Use steeper decay for values > 8.0
        if b_val <= 8.0:
            weight = math.exp(-0.15 * (b_val - 1.0))
        else:
            weight = math.exp(-0.25 * (b_val - 1.0))
        b_weights.append(weight)
    
    # Normalize separately for <= 8.0 and > 8.0 to get 90/10 split
    sum_low = sum(b_weights[i] for i, b_val in enumerate(b_values) if b_val <= 8.0)
    sum_high = sum(b_weights[i] for i, b_val in enumerate(b_values) if b_val > 8.0)
    
    # Scale to get 90/10 split
    for i, b_val in enumerate(b_values):
        if b_val <= 8.0:
            b_weights[i] = b_weights[i] * (0.9 / sum_low) if sum_low > 0 else 0
        else:
            b_weights[i] = b_weights[i] * (0.1 / sum_high) if sum_high > 0 else 0
    
    growth_peak_age = random.choices(b_values, weights=b_weights, k=1)[0]

    # ---- Weighted growth_k (k parameter: 1.1 to 3.0, steps 0.1) ----
    # More evenly split with larger probability around k=2
    k_values = [round(1.1 + i * 0.1, 1) for i in range(20)]  # 1.1, 1.2, ..., 3.0
    k_weights = []
    for k_val in k_values:
        # Gaussian-like distribution centered around k=2
        # Higher weight near k=2, decreasing as we move away
        distance_from_2 = abs(k_val - 2.0)
        weight = math.exp(-0.5 * (distance_from_2 ** 2) / 0.3)  # Gaussian with sigma ~0.55
        k_weights.append(weight)
    
    # Normalize weights
    k_sum = sum(k_weights)
    k_weights = [w / k_sum for w in k_weights]
    
    growth_shape = round(random.choices(k_values, weights=k_weights, k=1)[0], 1)

    # Growth width is now redundant (k replaces it), but keep for backwards compatibility
    # Calculate approximate width from k for display purposes
    # k=1.1 gives broad (~5 years), k=3.0 gives narrow (~3 years)
    # Linear interpolation: width = 5.0 - (k - 1.1) * (2.0 / 1.9)
    estimated_width = 5.0 - (growth_shape - 1.1) * (2.0 / 1.9)
    growth_width = round(max(3.0, min(5.0, estimated_width)), 1)

    # ---- Attributes via birth development ----
    attributes, birth_nominal_dp, birth_assigned_dp = apply_birth_development(
        is_gk=is_goalkeeper,
        potential=potential,
        birth_dev_pct=birth_dev_pct
    )
    
    non_playing = {a: clamp(int(random.gauss(10, 4))) for a in NON_PLAYING_ATTRIBUTES}
    
    position_traits = [random.choice(POSITION_TRAITS)]
    gainable_traits = random.sample(GAINABLE_TRAITS, k=random.randint(1, 3))
    
    # Generate nationality first, then use it for name generation
    if nationality is None:
        nationality = random.choice(NATIONALITIES)
    
    # Determine heritage origin country if heritage options provided
    # Determine heritage group for this player
    origin_country = None
    heritage_group = None
    name_structure = None  # Initialize name_structure
    name_pool_debug: Dict[str, str] = {}
    
    if heritage_options and len(heritage_options) > 0:
        origin_country = random.choice(heritage_options)
        # Map origin_country to heritage group
        if nationality == "ENG" and origin_country == "NGA":
            heritage_group = "ENG_WestAfrica"
        elif nationality == "ENG" and origin_country == "ENG":
            # ENG heritage for ENG nationality = mainstream
            heritage_group = "ENG_Mainstream"
    else:
        # No heritage options specified, use default heritage group selection
        from utils.name_generation import select_heritage_group
        heritage_group = select_heritage_group(nationality)
    
    # Generate name with heritage if origin_country is set
    if origin_country and origin_country != nationality:
        # For testing: use heritage naming by directly sampling from origin_country pools
        # This bypasses the heritage group system for simplicity
        from utils.name_generation import generate_name
        # Try to use a heritage group if available

        # If we have a valid heritage group, use it; otherwise fall back to simple mixing
        if heritage_group:
            name_obj = generate_name(
                nationality=nationality,
                heritage_group=heritage_group,
                origin_country=origin_country,
                used_names=None,
                name_pool_debug=name_pool_debug,
            )
            player_name = str(name_obj)
            name_structure = name_pool_debug.get("name_structure", "LL")
        else:
            # Simple 50/50 mix for testing when heritage group not configured
            from utils.name_data import tier_probs_for_pool
            from utils.name_generation import (
                get_name_pool,
                resolve_local_pool_id,
                sample_name_from_pool,
                name_structure_code,
                effective_surname_pool_for_sampling,
            )
            
            _lpid = resolve_local_pool_id(nationality)
            given_pool_nat = get_name_pool(_lpid, "given_names_male")
            _nat_sid, surname_pool_nat = effective_surname_pool_for_sampling(_lpid)
            _hpid = f"country_{origin_country}" if origin_country and len(origin_country) == 3 else origin_country
            given_pool_her = get_name_pool(_hpid, "given_names_male") if _hpid else None
            surname_pool_her = get_name_pool(_hpid, "surnames") if _hpid else None
            
            # 50% chance to use heritage for given name, 50% for surname
            given_country = origin_country if random.random() < 0.5 else nationality
            surname_country = origin_country if random.random() < 0.5 else nationality
            
            given_pool = given_pool_her if given_country == origin_country else given_pool_nat
            surname_pool = surname_pool_her if surname_country == origin_country else surname_pool_nat

            name_pool_debug.clear()
            name_pool_debug["mode"] = "heritage_mix_test"
            name_pool_debug["local_pool_id"] = _lpid
            name_pool_debug["heritage_pool_id"] = str(_hpid)
            name_pool_debug["given_sample_pool_id"] = str(
                _hpid if given_country == origin_country else _lpid
            )
            name_pool_debug["surname_sample_pool_id"] = str(
                _hpid if surname_country == origin_country else _lpid
            )
            
            given_pid_dbg = str(_hpid if given_country == origin_country else _lpid)
            surname_pid_dbg = str(_hpid if surname_country == origin_country else _lpid)
            given_tier_probs = tier_probs_for_pool(given_pid_dbg, given_country, "given")
            surname_tier_probs = tier_probs_for_pool(surname_pid_dbg, surname_country, "surname")
            
            given_first = (
                sample_name_from_pool(given_pool, given_tier_probs)
                if given_pool
                else ""
            )
            surname_first = (
                sample_name_from_pool(surname_pool, surname_tier_probs)
                if surname_pool
                else ""
            )
            if not (given_first or "").strip():
                given_first = "NoFirstName"
            if not (surname_first or "").strip():
                surname_first = "NoLastName"
            player_name = f"{given_first} {surname_first}"
            
            # Determine actual name structure based on what was used
            given_origin = "HERITAGE" if given_country == origin_country else "LOCAL"
            surname_origin = "HERITAGE" if surname_country == origin_country else "LOCAL"
            name_structure = name_structure_code(given_origin, surname_origin)
            name_pool_debug["name_structure"] = name_structure
    else:
        # When origin_country == nationality or no origin_country, use heritage_group if available
        # This ensures names match the heritage group used for profile pictures
        if heritage_group:
            from utils.name_generation import generate_name

            name_obj = generate_name(
                nationality=nationality,
                heritage_group=heritage_group,
                origin_country=None,  # No heritage origin when origin_country == nationality
                used_names=None,
                name_pool_debug=name_pool_debug,
            )
            player_name = str(name_obj)
            name_structure = name_pool_debug.get("name_structure", "LL")
        else:
            player_name = rnd_name(nationality=nationality, name_pool_debug=name_pool_debug)
            name_structure = name_pool_debug.get("name_structure", "LL")
    
    return {
        "name": player_name,
        "nationality": nationality,
        "heritage_group": heritage_group,  # Store heritage group for profile picture selection
        "name_structure": name_structure,  # Store name structure (LL, LH, HL, HH) for display
        "naming_pool_attempted": _format_naming_pool_attempted(name_pool_debug),
        "skin_tone": random.choice(SKIN_TONES),
        "is_goalkeeper": is_goalkeeper,
        "actual_age_months": actual_age_months,
        "training_age_weeks": training_age_weeks,
        "potential": potential,
        "birth_dev_pct": birth_dev_pct,
        "base_training_pct": base_training_pct,
        "growth_training_pct": growth_training_pct,
        "growth_shape": growth_shape,
        "growth_peak_age": growth_peak_age,
        "growth_width": growth_width,
        "attributes": attributes,
        "non_playing_attributes": non_playing,
        "position_traits": position_traits,
        "gainable_traits": gainable_traits,
    }
