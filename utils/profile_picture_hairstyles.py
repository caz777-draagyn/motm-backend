"""
Afro-lineage visual buckets: roll specialty hairstyle asset folders vs regular bucket.

Specialty folders live next to regional buckets under gfx/player_profile_pics/.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

# Buckets that use base specialty % + optional country modifiers
AFRO_LINEAGE_VISUAL_BUCKETS = frozenset(
    {
        "AfricaWest",
        "AfricaCentral",
        "AfricaEast",
        "AfricaSahelia",
        "AfricaSouth",
        "AfricaHorn",
        "AfroBrazil",
        "AfroBrazilian",
        "AfroCaribbean",
    }
)

# Base weights (%): short_locs, big_locs, cornrows, big_afro — remainder is "regular" bucket
_BASE_SPECIALTY_PCT: dict[str, Tuple[int, int, int, int]] = {
    "AfroCaribbean": (9, 6, 11, 8),
    "AfroBrazil": (5, 3, 6, 6),
    "AfroBrazilian": (5, 3, 6, 6),
    "AfricaWest": (5, 3, 11, 4),
    "AfricaCentral": (4, 3, 8, 3),
    "AfricaEast": (3, 1, 4, 2),
    "AfricaSouth": (4, 2, 5, 3),
    "AfricaSahelia": (3, 1, 4, 2),
    "AfricaHorn": (1, 0, 1, 0),
}

# gfx path segments under player_profile_pics/ (same order as tuple above)
_SPECIALTY_FOLDER_NAMES = ("hairshortloc", "hairbigloc", "cornrows", "HairBigAfro")

# When nationality matches and visual bucket matches, add these deltas (percentage points) to each specialty
_COUNTRY_SPECIALTY_DELTAS: List[Tuple[str, str, Tuple[int, int, int, int]]] = [
    ("JAM", "AfroCaribbean", (1, 1, 1, 1)),
    ("TTO", "AfroCaribbean", (-1, -2, -2, -2)),
    ("BRB", "AfroCaribbean", (-2, -2, -3, -2)),
    ("SUR", "AfroCaribbean", (-2, -2, -3, -3)),
    ("SEN", "AfricaWest", (-1, -1, -2, -1)),
    ("GAM", "AfricaWest", (-1, -1, -2, -1)),
    ("GNB", "AfricaWest", (-1, -1, -2, -1)),
]


def visual_bucket_from_picture_rel(rel: str) -> Optional[str]:
    """Last path segment of ``player_profile_pics/<VisualBucket>``."""
    norm = rel.replace("\\", "/").strip("/")
    parts = norm.split("/")
    if len(parts) >= 2 and parts[0] == "player_profile_pics":
        return parts[-1]
    return None


def _country_deltas(nationality: Optional[str], visual_bucket: str) -> Tuple[int, int, int, int]:
    if not nationality:
        return (0, 0, 0, 0)
    u = nationality.strip().upper()
    for code, vb, deltas in _COUNTRY_SPECIALTY_DELTAS:
        if code == u and vb == visual_bucket:
            return deltas
    return (0, 0, 0, 0)


def _adjusted_specialty_pcts(visual_bucket: str, nationality: Optional[str]) -> Tuple[int, int, int, int]:
    base = _BASE_SPECIALTY_PCT.get(visual_bucket)
    if base is None:
        return (0, 0, 0, 0)
    d = _country_deltas(nationality, visual_bucket)
    return tuple(max(0, base[i] + d[i]) for i in range(4))


def roll_player_profile_pics_rel(base_rel: str, nationality: Optional[str]) -> str:
    """
    Given the resolved heritage picture path (e.g. ``player_profile_pics/AfricaWest``),
    optionally redirect to a global specialty folder. When ``nationality`` is None, always
    returns ``base_rel`` (no hairstyle roll — used for legacy fallbacks).
    """
    vb = visual_bucket_from_picture_rel(base_rel)
    if vb is None or vb not in AFRO_LINEAGE_VISUAL_BUCKETS:
        return base_rel
    if nationality is None:
        return base_rel
    if vb not in _BASE_SPECIALTY_PCT:
        return base_rel

    short_l, big_l, corn, big_a = _adjusted_specialty_pcts(vb, nationality)
    regular = max(0, 100 - (short_l + big_l + corn + big_a))

    choices: List[str] = [base_rel]
    weights: List[int] = [regular]
    for name, w in zip(_SPECIALTY_FOLDER_NAMES, (short_l, big_l, corn, big_a)):
        choices.append(f"player_profile_pics/{name}")
        weights.append(w)

    filtered = [(c, w) for c, w in zip(choices, weights) if w > 0]
    if not filtered:
        return base_rel
    c_list, w_list = zip(*filtered)
    return random.choices(c_list, weights=w_list, k=1)[0]
