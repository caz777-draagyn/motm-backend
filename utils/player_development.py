"""
Player development module: Training and attribute progression system.
Based on the PlayerGenAndTraining notebook.
"""

import random
import math
from typing import Any, Dict, Optional, List, Tuple
from match_engine.constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS


def _make_outfield_program(weights: Dict[str, float], *, filler: float = 0.0) -> Dict[str, float]:
    """
    Build a complete outfield programme vector over all attributes.

    By default, unspecified attributes are 0.0. For named programmes we often
    provide a small non-zero filler to avoid over-concentrating training on only
    4–5 attributes.
    """
    d = {a: float(filler) for a in OUTFIELD_ATTRS}
    for k, v in weights.items():
        if k not in d:
            raise ValueError(f"Unknown outfield attribute in training program: {k}")
        d[k] = float(v)
    return d


# Training program definitions — percentage weights per programme (sparse attrs are 0). Outfield only.
OUTFIELD_PROGRAMS: Dict[str, Dict[str, float]] = {
    "Balanced": {a: 1.0 for a in OUTFIELD_ATTRS},
    "Marking Focus": _make_outfield_program(
        {"Tackling": 15, "Marking": 30, "Composure": 15, "Positioning": 25, "Work Rate": 15},
        filler=5.0,
    ),
    "Tackling Focus": _make_outfield_program(
        {"Acceleration": 15, "Strength": 20, "Tackling": 30, "Marking": 20, "Work Rate": 15},
        filler=5.0,
    ),
    "Defensive Dueling": _make_outfield_program(
        {"Jump Reach": 15, "Strength": 25, "Heading": 15, "Tackling": 25, "Marking": 20},
        filler=5.0,
    ),
    "Wide Defending": _make_outfield_program(
        {"Acceleration": 30, "Agility": 20, "Stamina": 15, "Tackling": 25, "Marking": 10},
        filler=5.0,
    ),
    "Passing Focus": _make_outfield_program(
        {
            "Ball Control": 25,
            "Passing": 30,
            "Composure": 15,
            "Positioning": 10,
            "Vision": 20,
        },
        filler=5.0,
    ),
    "Crossing Focus": _make_outfield_program(
        {
            "Acceleration": 15,
            "Ball Control": 20,
            "Crossing": 30,
            "Passing": 20,
            "Vision": 15,
        },
        filler=5.0,
    ),
    "Engine": _make_outfield_program(
        {"Agility": 15, "Stamina": 20, "Strength": 30, "Positioning": 10, "Work Rate": 25},
        filler=5.0,
    ),
    "Finishing Focus": _make_outfield_program(
        {
            "Acceleration": 10,
            "Ball Control": 15,
            "Finishing": 30,
            "Composure": 25,
            "Positioning": 20,
        },
        filler=5.0,
    ),
    "Heading Focus": _make_outfield_program(
        {"Stamina": 25, "Strength": 20, "Heading": 30, "Composure": 10, "Positioning": 15},
        filler=5.0,
    ),
    "Chance Creation": _make_outfield_program(
        {
            "Agility": 15,
            "Ball Control": 20,
            "Passing": 25,
            "Composure": 15,
            "Vision": 25,
        },
        filler=5.0,
    ),
    "Progression": _make_outfield_program(
        {
            "Ball Control": 25,
            "Finishing": 15,
            "Passing": 25,
            "Composure": 15,
            "Vision": 20,
        },
        filler=5.0,
    ),
    "Explosive Movement": _make_outfield_program(
        {"Acceleration": 30, "Agility": 40, "Stamina": 15, "Work Rate": 15},
        filler=5.0,
    ),
    "Physical Presence": _make_outfield_program(
        {"Jump Reach": 30, "Strength": 35, "Heading": 20, "Composure": 15},
        filler=5.0,
    ),
    "Wide Delivery": _make_outfield_program(
        {"Ball Control": 20, "Crossing": 40, "Passing": 20, "Vision": 20},
        filler=5.0,
    ),
}

INDIVIDUAL_PROGRAM_NAME = "Individual"


def resolve_outfield_program(name: str, *, individual_attr: Optional[str] = None) -> Optional[Dict[str, float]]:
    """
    Return weight dict for a named outfield programme, or None if unknown.

    Supports the single programme name ``Individual`` with a separately provided
    ``individual_attr`` selection.
    """
    n = name.strip()
    if n in OUTFIELD_PROGRAMS:
        return OUTFIELD_PROGRAMS[n]
    if n == INDIVIDUAL_PROGRAM_NAME:
        attr = (individual_attr or "").strip()
        if attr in OUTFIELD_ATTRS:
            return _make_outfield_program({attr: 100.0}, filler=5.0)
    return None


def is_individual_program_name(name: Optional[str]) -> bool:
    return bool(
        name
        and name.strip() == INDIVIDUAL_PROGRAM_NAME
    )


def individual_training_dp_multiplier(
    primary_name: Optional[str], secondary_name: Optional[str]
) -> float:
    """
    Weekly DP multiplier for outfield when Individual: <attr> programmes are selected.
    Primary only: -10%; secondary only: -7%; both: -20% (single rule, not multiplicative).
    """
    p = is_individual_program_name(primary_name)
    s = is_individual_program_name(secondary_name)
    if p and s:
        return 0.80
    if p:
        return 0.90
    if s:
        return 0.93
    return 1.0


def list_training_program_names(is_goalkeeper: bool) -> List[str]:
    """Valid training programme names for API validation and clients."""
    if is_goalkeeper:
        return sorted(GK_PROGRAMS.keys())
    return sorted(list(OUTFIELD_PROGRAMS.keys()) + [INDIVIDUAL_PROGRAM_NAME])

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


def _uniform_distribution(player_attrs: List[str]) -> Dict[str, float]:
    """Equal probability over all attributes (sums to 1)."""
    n = len(player_attrs)
    if n <= 0:
        return {}
    u = 1.0 / n
    return {a: u for a in player_attrs}


def _normalize_program_to_distribution(
    programme: Optional[Dict[str, float]],
    player_attrs: List[str],
) -> Optional[Dict[str, float]]:
    """
    Map a raw programme vector to a distribution over player_attrs (sums to 1).
    Specialist programmes use large raw weights (e.g. 10–30) while uniform uses 1/n;
    normalizing before mixing makes primary/secondary/general shares interpretable.
    """
    if not programme:
        return None
    sub = {k: float(programme.get(k, 0.0)) for k in player_attrs}
    total = sum(sub.values())
    if total <= 1e-12:
        return _uniform_distribution(player_attrs)
    inv = 1.0 / total
    return {k: sub[k] * inv for k in player_attrs}


def get_program_catalog(is_goalkeeper: bool) -> Dict[str, Dict[str, float]]:
    """Get the appropriate program catalog for player type."""
    return GK_PROGRAMS if is_goalkeeper else OUTFIELD_PROGRAMS


def get_general_program(is_goalkeeper: bool) -> Dict[str, float]:
    """General training program: equal probability over all attributes (sums to 1)."""
    attrs = GOALKEEPER_ATTRS if is_goalkeeper else OUTFIELD_ATTRS
    return _uniform_distribution(attrs)


def build_program_mix_weights(
    player_attrs: List[str],
    is_goalkeeper: bool,
    *,
    primary_name: Optional[str],
    primary_share: float,
    primary_individual_attr: Optional[str] = None,
    secondary_name: Optional[str],
    secondary_share: float,
    secondary_individual_attr: Optional[str] = None,
    general_share: float
) -> Dict[str, float]:
    """
    Blend primary, secondary, and general training programmes.

    Each programme is first converted to a distribution over attributes (sums to 1). Raw
    catalogue weights (e.g. 30 for Finishing) only matter relative to each other within
    that programme; uniform general uses 1/n per attribute. Then:

        final = p_share * norm(primary) + s_share * norm(secondary) + g_share * norm(uniform)

    Shares can be any non-negative numbers; they are normalized to sum to 1.
    """
    # Normalize mix shares
    total_share = max(1e-9, primary_share + secondary_share + general_share)
    p_share = primary_share / total_share
    s_share = secondary_share / total_share
    g_share = general_share / total_share

    if is_goalkeeper:
        primary = GK_PROGRAMS.get(primary_name) if primary_name else None
        secondary = GK_PROGRAMS.get(secondary_name) if secondary_name else None
    else:
        primary = (
            resolve_outfield_program(primary_name, individual_attr=primary_individual_attr)
            if primary_name
            else None
        )
        secondary = (
            resolve_outfield_program(secondary_name, individual_attr=secondary_individual_attr)
            if secondary_name
            else None
        )

    norm_p = _normalize_program_to_distribution(primary, player_attrs) if primary else None
    norm_s = _normalize_program_to_distribution(secondary, player_attrs) if secondary else None
    norm_g = _uniform_distribution(player_attrs)

    final_weights: Dict[str, float] = uniform_weights_for(player_attrs, 0.0)
    for k in player_attrs:
        if norm_p is not None:
            final_weights[k] += p_share * norm_p[k]
        if norm_s is not None:
            final_weights[k] += s_share * norm_s[k]
        final_weights[k] += g_share * norm_g[k]

    # Safety: if everything became 0, fall back to uniform
    if sum(final_weights.values()) <= 1e-12:
        # If primary/secondary were None and g_share was 0, rare edge case
        return _uniform_distribution(player_attrs)

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
    primary_program: Optional[str] = "Finishing Focus",
    primary_share: float = 0.4,
    primary_individual_attr: Optional[str] = None,
    secondary_program: Optional[str] = "Passing Focus",
    secondary_share: float = 0.3,
    secondary_individual_attr: Optional[str] = None,
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
        primary_individual_attr=primary_individual_attr,
        secondary_name=secondary_program,
        secondary_share=secondary_share,
        secondary_individual_attr=secondary_individual_attr,
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
    primary_program: Optional[str] = "Tackling Focus",
    primary_share: float = 0.4,
    primary_individual_attr: Optional[str] = None,
    secondary_program: Optional[str] = "Heading Focus",
    secondary_share: float = 0.2,
    secondary_individual_attr: Optional[str] = None,
    general_share: float = 0.4,
    season_weeks: int = 10,
    total_weeks: int = 160,
    DP_PER_ATTR_POINT: float = 10.0,
    program_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Tuple[float, float]]:
    """
    Train multiple players for one season.

    program_overrides: optional map player_id -> {primary_program, secondary_program,
    primary_share, secondary_share, general_share} for per-player training mixes.
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
            ov = (program_overrides or {}).get(player_id) or {}
            pp = ov.get("primary_program", primary_program)
            ps = float(ov.get("primary_share", primary_share))
            pia = ov.get("primary_individual_attr", primary_individual_attr)
            sp = ov.get("secondary_program", secondary_program)
            ss = float(ov.get("secondary_share", secondary_share))
            sia = ov.get("secondary_individual_attr", secondary_individual_attr)
            gs = float(ov.get("general_share", general_share))
            nom, asg = train_player_week(
                player,
                growth_weights_cache=growth_caches[player_id],
                train_carry=train_carries[player_id],
                training_facilities_level=training_facilities_level,
                primary_program=pp,
                primary_share=ps,
                primary_individual_attr=pia,
                secondary_program=sp,
                secondary_share=ss,
                secondary_individual_attr=sia,
                general_share=gs,
                total_weeks=total_weeks,
                DP_PER_ATTR_POINT=DP_PER_ATTR_POINT
            )
            n0, a0 = per_player_totals[player_id]
            per_player_totals[player_id] = (n0 + nom, a0 + asg)

    for player in players:
        tick_offseason(player)

    return {pid: (round(n, 1), round(a, 1)) for pid, (n, a) in per_player_totals.items()}
