"""
Rarity tier probability profiles for name pools.

Head weights (percent of total draw) match design tables; tail uses remaining mass
split by pool size. See scripts/apply_pool_tier_probs.py and plan docs.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .name_data import NAME_POOL_TIER_KEYS

_HEAD_KEYS = ("top", "very_common", "common", "familiar")

# Given names — percent of total for each head tier (sum = head total; tail = 100 - sum)
GIVEN_HEAD: Dict[str, Tuple[int, int, int, int]] = {
    "CONCENTRATED": (22, 15, 12, 11),
    "MEDIUM": (11, 12, 12, 15),
    "BROAD": (7, 9, 9, 15),
    "TINY": (10, 15, 20, 55),
}

# Surnames
SURNAME_HEAD: Dict[str, Tuple[int, int, int, int]] = {
    "CONCENTRATED": (17, 21, 18, 19),
    "MEDIUM": (13, 17, 16, 19),
    "BROAD": (9, 13, 14, 19),
    "TINY": (10, 15, 20, 55),
}

_PROFILE_ALIASES = {"MANUAL": "SPECIAL"}

EPS = 1e-12


def normalize_profile_token(raw: str) -> str:
    s = (raw or "").strip().upper()
    return _PROFILE_ALIASES.get(s, s)


def _normalize_prob_dict(d: Dict[str, float]) -> Dict[str, float]:
    s = sum(max(0.0, float(d.get(k, 0.0))) for k in NAME_POOL_TIER_KEYS)
    if s <= EPS:
        u = 1.0 / len(NAME_POOL_TIER_KEYS)
        return {k: u for k in NAME_POOL_TIER_KEYS}
    return {k: max(0.0, float(d.get(k, 0.0))) / s for k in NAME_POOL_TIER_KEYS}


def compute_tier_probs(branch: str, profile: str, n_total: int) -> Dict[str, float]:
    """
    Build seven-tier probabilities summing to 1.

    :param branch: ``\"given\"`` or ``\"surname\"``.
    :param profile: ``CONCENTRATED``, ``MEDIUM``, ``BROAD``, ``TINY`` (not ``SPECIAL``).
    :param n_total: total name count in that branch (all seven tiers).
    """
    prof = normalize_profile_token(profile)
    if prof == "SPECIAL":
        raise ValueError("SPECIAL profile must use hand-written tier_probs in JSON, not compute_tier_probs()")

    table = GIVEN_HEAD if branch == "given" else SURNAME_HEAD
    if prof not in table:
        prof = "MEDIUM"

    out: Dict[str, float] = {k: 0.0 for k in NAME_POOL_TIER_KEYS}

    # Under 150 names: force TINY head (100% in first four tiers, 0 tail)
    if n_total < 150:
        heads = table["TINY"]
    else:
        heads = table[prof]

    hsum_pct = sum(heads)
    for i, k in enumerate(_HEAD_KEYS):
        out[k] = heads[i] / 100.0

    # TINY (or forced tiny): head sums to 100%
    if abs(hsum_pct - 100.0) < 1e-9:
        return _normalize_prob_dict(out)

    tail_mass = 1.0 - hsum_pct / 100.0
    if tail_mass <= EPS:
        return _normalize_prob_dict(out)

    # very_rare only gets tail share when N > 2000 (three-way split)
    if n_total > 2000:
        out["uncommon"] += tail_mass * 0.4
        out["rare"] += tail_mass * 0.4
        out["very_rare"] += tail_mass * 0.2
    elif n_total >= 501:
        out["uncommon"] += tail_mass * 0.4
        out["rare"] += tail_mass * 0.6
    elif n_total >= 150:
        out["uncommon"] += tail_mass * 1.0

    return _normalize_prob_dict(out)


def merge_zero_prob_tiers(
    name_pool: Dict[str, List[str]],
    tier_probs: Dict[str, float],
) -> Tuple[Dict[str, List[str]], Dict[str, float]]:
    """
    Copy tier lists; for any tier with probability <= 0 but non-empty names, append those
    names to the nearest more-common tier (toward ``top``) that has p > 0. If none, merge
    into ``top`` so names remain drawable.
    """
    keys = NAME_POOL_TIER_KEYS
    p = {k: float(tier_probs.get(k, 0.0)) for k in keys}
    eff: Dict[str, List[str]] = {k: [x for x in (name_pool.get(k) or []) if isinstance(x, str)] for k in keys}

    for i in range(len(keys) - 1, -1, -1):
        tier = keys[i]
        if p[tier] > EPS or not eff[tier]:
            continue
        dest_idx = None
        for j in range(i - 1, -1, -1):
            if p[keys[j]] > EPS:
                dest_idx = j
                break
        if dest_idx is None:
            dest_idx = 0
        dest = keys[dest_idx]
        eff[dest].extend(eff[tier])
        eff[tier] = []

    return eff, p


def count_branch_names(block: object) -> int:
    if not isinstance(block, dict):
        return 0
    return sum(len(block.get(k) or []) for k in NAME_POOL_TIER_KEYS if isinstance(block.get(k), list))
