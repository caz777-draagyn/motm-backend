"""
Player development module: Training and attribute progression system.
Based on the PlayerGenAndTraining notebook.
"""

import random
import math
from typing import Dict, Optional, List, Tuple
from match_engine.constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS

# Training program definitions - these use match_engine constants for attribute names
OUTFIELD_PROGRAMS: Dict[str, Dict[str, float]] = {
    "Balanced": {a: 1.0 for a in OUTFIELD_ATTRS},
    "Finishing": {
        **{a: 0.3 for a in OUTFIELD_ATTRS},
        "Finishing": 4.0
    },
    "Playmaking": {
        **{a: 0.3 for a in OUTFIELD_ATTRS},
        "Passing": 3.0, "Vision": 3.0, "Ball Control": 2.0, "Composure": 1.5
    },
    "Defending": {
        **{a: 0.3 for a in OUTFIELD_ATTRS},
        "Tackling": 3.0, "Marking": 3.0, "Positioning": 2.0, "Strength": 1.5
    },
    "Pace & Power": {
        **{a: 0.3 for a in OUTFIELD_ATTRS},
        "Acceleration": 3.0, "Agility": 2.0, "Stamina": 2.0, "Strength": 2.0
    },
    "Aerial": {
        **{a: 0.3 for a in OUTFIELD_ATTRS},
        "Heading": 3.0, "Jump Reach": 3.0, "Strength": 1.5, "Positioning": 1.5
    },
    "Crossing & Wide": {
        **{a: 0.3 for a in OUTFIELD_ATTRS},
        "Crossing": 3.0, "Acceleration": 2.0, "Ball Control": 1.5, "Vision": 1.5
    },
}

GK_PROGRAMS: Dict[str, Dict[str, float]] = {
    "Balanced": {a: 1.0 for a in GOALKEEPER_ATTRS},
    "Shot-Stopping": {
        **{a: 0.7 for a in GOALKEEPER_ATTRS},
        "Reflexes": 3.0, "Handling": 2.5, "Agility": 2.0, "Composure": 1.5
    },
    "Sweeper Keeper": {
        **{a: 0.7 for a in GOALKEEPER_ATTRS},
        # Note: Match engine doesn't have "Communication", "Kicking", "Throwing"
        # Using Positioning as alternative
        "Positioning": 2.5, "Composure": 2.0, "Work Rate": 2.0
    },
    "Aerial/High Claims": {
        **{a: 0.7 for a in GOALKEEPER_ATTRS},
        "Aerial Reach": 3.0, "Handling": 2.0, "Strength": 1.5, "Positioning": 1.5
    },
}


def training_facility_multiplier(level: int, max_level: int = 10, floor: float = 0.5) -> float:
    """
    Multiplier applied to the weekly DP. 
    - At max level → 1.0
    - At level 0   → 'floor' (default 0.5)
    Linear between floor..1.0
    """
    level = max(0, min(max_level, int(level)))
    return floor + (1.0 - floor) * (level / max_level)


def uniform_weights_for(player_attrs: List[str], val: float = 1.0) -> Dict[str, float]:
    """Generate uniform weights for all attributes."""
    return {a: val for a in player_attrs}


def get_program_catalog(is_goalkeeper: bool) -> Dict[str, Dict[str, float]]:
    """Get the appropriate program catalog for player type."""
    return GK_PROGRAMS if is_goalkeeper else OUTFIELD_PROGRAMS


def get_general_program(is_goalkeeper: bool) -> Dict[str, float]:
    """General training program (equal weights for all attributes)."""
    attrs = GOALKEEPER_ATTRS if is_goalkeeper else OUTFIELD_ATTRS
    weight = 1.0 / len(attrs)
    return {a: weight for a in attrs}


def build_program_mix_weights(
    player_attrs: List[str],
    is_goalkeeper: bool,
    *,
    primary_name: Optional[str],
    primary_share: float,
    secondary_name: Optional[str],
    secondary_share: float,
    general_share: float
) -> Dict[str, float]:
    """
    Final attribute weights = primary_share * primary_prog
                            + secondary_share * secondary_prog
                            + general_share * uniform
    Shares can be any non-negative numbers; they will be normalized.
    """
    # Normalize shares
    total_share = max(1e-9, primary_share + secondary_share + general_share)
    p_share = primary_share / total_share
    s_share = secondary_share / total_share
    g_share = general_share / total_share

    catalog = get_program_catalog(is_goalkeeper)
    primary = catalog.get(primary_name, None) if primary_name else None
    secondary = catalog.get(secondary_name, None) if secondary_name else None
    general = uniform_weights_for(player_attrs, 1.0)

    # Start from zeros
    final_weights: Dict[str, float] = uniform_weights_for(player_attrs, 0.0)

    # Add weighted programs
    if primary:
        for k, v in primary.items():
            if k in final_weights:
                final_weights[k] = final_weights.get(k, 0.0) + p_share * float(v)
    if secondary:
        for k, v in secondary.items():
            if k in final_weights:
                final_weights[k] = final_weights.get(k, 0.0) + s_share * float(v)
    # General (uniform)
    for k, v in general.items():
        final_weights[k] = final_weights.get(k, 0.0) + g_share * float(v)

    # Safety: if everything became 0, fall back to uniform
    if sum(final_weights.values()) <= 0:
        final_weights = general

    return final_weights


def choose_training_attribute(
    attributes: Dict[str, int],
    attrs_list: List[str],
    weights: Optional[Dict[str, float]]
) -> Optional[str]:
    """Choose an attribute for training based on weights, excluding capped attributes."""
    # Filter out capped
    candidates = [(a, max(0.0, (weights or {}).get(a, 1.0))) for a in attrs_list if attributes.get(a, 0) < 20]
    if not candidates:
        return None
    names, w = zip(*candidates)
    total = sum(w)
    if total <= 0:
        names = [a for a in attrs_list if attributes.get(a, 0) < 20]
        return random.choice(names) if names else None
    r = random.uniform(0, total)
    cum = 0.0
    for name, ww in candidates:
        cum += ww
        if r <= cum:
            return name
    return candidates[-1][0] if candidates else None


def weibull_pdf_months(x_months: int, k: float, b: float) -> float:
    """
    Weibull PDF for growth distribution.
    Reparameterized: a = k * b, where k controls width and b is peak age.
    """
    if x_months <= 0 or k <= 0 or b <= 0:
        return 0.0
    a = k * b  # Shape parameter = k * scale parameter
    x10 = x_months / 10.0
    scale = 10.0 * (b ** a)
    return (a / scale) * (x10 ** (a - 1.0)) * math.exp(-((x10 / b) ** a))


def compile_growth_schedule(
    growth_shape: float,
    growth_peak_age: float,
    total_weeks: int = 160
) -> List[float]:
    """
    Normalized weights for growth DP across training weeks (16->32y).
    
    Args:
        growth_shape: The k parameter (ranges 1.1-3.0). Controls width of distribution.
        growth_peak_age: The b parameter (ranges 1.0-10.0). Peak growth age in years.
    
    The Weibull shape parameter a = k * b, where k = growth_shape and b = growth_peak_age.
    """
    k = max(1.1, float(growth_shape))  # k ranges from 1.1 to 3.0
    b = max(1.0, float(growth_peak_age))  # b ranges from 1.0 to 10.0

    weights = [weibull_pdf_months(wk, k, b) for wk in range(1, total_weeks + 1)]
    s = sum(weights) or 1.0
    return [w / s for w in weights]


def _assign_chunk_with_efficiency(
    attributes: Dict[str, int],
    attrs_list: List[str],
    train_carry: Dict[str, float],
    chunk: float,
    weights: Optional[Dict[str, float]] = None
) -> Tuple[float, float]:
    """
    Try to assign 'chunk' DP to a weighted random attribute using efficiency bands.
    Returns (nominal_used, assigned_dp).
    If we pick a 20-rated attr, we reroll without consuming nominal.
    """
    # Pick attribute using weights (fall back to random)
    a = choose_training_attribute(attributes, attrs_list, weights)
    if a is None:
        # fallback: pick any non-20
        candidates = [attr for attr in attrs_list if attributes.get(attr, 0) < 20]
        if not candidates:
            return (0.0, 0.0)
        a = random.choice(candidates)

    val = attributes.get(a, 0)
    
    # Efficiency rules
    if 1 <= val <= 5:
        assigned = chunk * (2 if random.random() < 0.5 else 1)
        nominal = chunk
    elif 6 <= val <= 15:
        assigned = chunk
        nominal = chunk
    elif 16 <= val <= 17:
        assigned = chunk if random.random() < 0.5 else 0.0
        nominal = chunk
    elif 18 <= val <= 19:
        assigned = chunk if random.random() < 0.33 else 0.0
        nominal = chunk
    else:  # val == 20
        return (0.0, 0.0)

    # Track carry for delayed conversion
    train_carry[a] = train_carry.get(a, 0.0) + assigned
    return (nominal, assigned)


def _convert_carry_to_attributes(
    attributes: Dict[str, int],
    train_carry: Dict[str, float],
    DP_PER_ATTR_POINT: float = 10.0
) -> None:
    """Convert carry to real +1s as long as thresholds are reached, capping at 20."""
    for a in train_carry:
        while train_carry[a] >= DP_PER_ATTR_POINT and attributes.get(a, 0) < 20:
            attributes[a] = attributes.get(a, 0) + 1
            train_carry[a] -= DP_PER_ATTR_POINT


def train_player_week(
    player,
    growth_weights_cache: List[float],
    train_carry: Dict[str, float],
    *,
    training_facilities_level: int = 10,
    primary_program: Optional[str] = "Finishing",
    primary_share: float = 0.4,
    secondary_program: Optional[str] = "Finishing",
    secondary_share: float = 0.3,
    general_share: float = 0.3,
    total_weeks: int = 160,
    DP_PER_ATTR_POINT: float = 10.0,
    chunk_min: float = 0.1,
    chunk_max: float = 0.5,
) -> Tuple[float, float]:
    """
    One in-season training week with:
      - Facilities multiplier
      - Program mix (primary/secondary/general)
      - Same efficiency rules & chunking
    
    Args:
        player: SQLAlchemy Player model instance
        growth_weights_cache: Pre-computed growth weights list
        train_carry: Dict to track DP carry per attribute (persistent across calls)
        ... (other params)
    
    Returns (nominal_used, assigned_dp).
    """
    # Get player attributes dict (ensure it exists)
    if player.attributes is None:
        attrs_list = GOALKEEPER_ATTRS if player.is_goalkeeper else OUTFIELD_ATTRS
        player.attributes = {a: 1 for a in attrs_list}
    
    attrs_list = GOALKEEPER_ATTRS if player.is_goalkeeper else OUTFIELD_ATTRS
    attributes = player.attributes  # Reference to the dict
    
    # Build mixed program weights
    prog_weights = build_program_mix_weights(
        attrs_list,
        player.is_goalkeeper,
        primary_name=primary_program,
        primary_share=primary_share,
        secondary_name=secondary_program,
        secondary_share=secondary_share,
        general_share=general_share
    )

    # Pools
    total_base = player.potential * player.base_training_pct
    total_growth = player.potential * player.growth_training_pct

    base_this_week = total_base / total_weeks if player.training_age_weeks < total_weeks else 0.0
    idx = max(0, min(total_weeks - 1, player.training_age_weeks))
    growth_this_week = total_growth * (growth_weights_cache[idx] if player.training_age_weeks < total_weeks else 0.0)

    dp_week = base_this_week + growth_this_week
    dp_week *= training_facility_multiplier(training_facilities_level)  # facilities penalty

    nominal_used = 0.0
    assigned_dp = 0.0
    budget = dp_week
    safety = 0

    retry = 0
    while budget - nominal_used >= chunk_min - 1e-9 and safety < 4000:
        safety += 1
        chunk = min(budget - nominal_used, random.uniform(chunk_min, chunk_max))

        used, got = _assign_chunk_with_efficiency(attributes, attrs_list, train_carry, chunk, prog_weights)
        if used == 0.0 and got == 0.0:
            retry += 1
            if retry < 12:
                continue  # try again with a new pick
            else:
                break      # likely all near-cap with heavy losses
        retry = 0

        nominal_used += used
        assigned_dp += got
        _convert_carry_to_attributes(attributes, train_carry, DP_PER_ATTR_POINT)
    
    # Update player age and training weeks (tick_training_week)
    player.actual_age_months = (player.actual_age_months or 0) + 1
    player.training_age_weeks = (player.training_age_weeks or 0) + 1
    
    # Update the player's attributes back (SQLAlchemy should handle JSONB updates)
    player.attributes = attributes
    
    return (round(nominal_used, 3), round(assigned_dp, 3))


def tick_offseason(player) -> None:
    """Off-season progression: +2 actual months, +0 training weeks."""
    player.actual_age_months = (player.actual_age_months or 0) + 2


def train_one_season_with_growth(
    players: List,
    growth_caches: Dict[str, List[float]],
    train_carries: Dict[str, Dict[str, float]],
    *,
    training_facilities_level: int = 10,
    primary_program: Optional[str] = "Defending",
    primary_share: float = 0.4,
    secondary_program: Optional[str] = "Aerial",
    secondary_share: float = 0.2,
    general_share: float = 0.4,
    season_weeks: int = 10,
    total_weeks: int = 160,
    DP_PER_ATTR_POINT: float = 10.0,
) -> Dict[str, Tuple[float, float]]:
    """
    Train multiple players for one season.
    
    Args:
        players: List of SQLAlchemy Player model instances
        growth_caches: Dict mapping player_id -> growth weights list
        train_carries: Dict mapping player_id -> train_carry dict (persistent)
    
    Returns Dict mapping player_id -> (nominal_total, assigned_total)
    """
    per_player_totals: Dict[str, Tuple[float, float]] = {}

    for player in players:
        player_id = str(player.id)
        per_player_totals[player_id] = (0.0, 0.0)
        
        # Ensure train_carry exists for this player
        if player_id not in train_carries:
            attrs_list = GOALKEEPER_ATTRS if player.is_goalkeeper else OUTFIELD_ATTRS
            train_carries[player_id] = {a: 0.0 for a in attrs_list}

    for _ in range(season_weeks):
        for player in players:
            player_id = str(player.id)
            nom, asg = train_player_week(
                player,
                growth_weights_cache=growth_caches[player_id],
                train_carry=train_carries[player_id],
                training_facilities_level=training_facilities_level,
                primary_program=primary_program,
                primary_share=primary_share,
                secondary_program=secondary_program,
                secondary_share=secondary_share,
                general_share=general_share,
                total_weeks=total_weeks,
                DP_PER_ATTR_POINT=DP_PER_ATTR_POINT
            )
            n0, a0 = per_player_totals[player_id]
            per_player_totals[player_id] = (n0 + nom, a0 + asg)

    for player in players:
        tick_offseason(player)

    return {pid: (round(n, 1), round(a, 1)) for pid, (n, a) in per_player_totals.items()}
