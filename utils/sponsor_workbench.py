"""
Sponsor workbench utility logic.

This module is intentionally in-memory and configuration-driven so balancing can
be tuned quickly before a database-backed implementation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple


WEEKS_PER_YEAR = 35
NEGOTIATION_PENALTY_RATE = 0.10
WEEKLY_CANCEL_RATE = 0.10

GUARANTEED_TYPE_MULTIPLIERS: Dict[str, float] = {
    "upfront": 0.8,
    "weekly": 1.0,
    "end_lump": 1.2,
}

GUARANTEED_TYPE_LABELS: Dict[str, str] = {
    "upfront": "Upfront lump sum",
    "weekly": "Weekly equal payout",
    "end_lump": "End-of-contract lump sum",
}

TARGET_LIBRARY: List[Dict[str, object]] = [
    {"code": "league_win", "label": "Win league title", "weight": 2.4},
    {"code": "cup_win", "label": "Win domestic cup", "weight": 2.2},
    {"code": "league_top3", "label": "Finish top 3 in league", "weight": 1.8},
    {"code": "player_20_goals", "label": "Have a player score 20+ league goals", "weight": 1.4},
    {"code": "clean_sheets_12", "label": "Keep 12+ clean sheets in league", "weight": 1.3},
    {"code": "cup_semifinal", "label": "Reach domestic cup semifinal", "weight": 1.2},
]


@dataclass
class OfferGenerationConfig:
    week_number: int = 1
    facility_level: int = 5
    staff_level: int = 5
    min_potential: int = 1
    max_potential: int = 20
    min_guaranteed_share: float = 0.25
    max_guaranteed_share: float = 0.75
    min_targets_per_offer: int = 1
    max_targets_per_offer: int = 3
    min_offer_count: int = 1
    max_offer_count: int = 8
    yearly_base_floor: int = 60000
    yearly_base_ceiling: int = 1400000


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def map_potential_to_yearly_base(potential: int, cfg: OfferGenerationConfig) -> int:
    """
    Map base potential (1-20) to yearly base money using linear interpolation.
    """
    bounded = clamp(potential, cfg.min_potential, cfg.max_potential)
    span = cfg.max_potential - cfg.min_potential
    if span <= 0:
        return cfg.yearly_base_floor
    ratio = (bounded - cfg.min_potential) / span
    return int(round(cfg.yearly_base_floor + ratio * (cfg.yearly_base_ceiling - cfg.yearly_base_floor)))


def compute_offer_count(cfg: OfferGenerationConfig) -> int:
    """
    Weekly offer count influenced by facilities and staff.
    """
    strength = clamp(cfg.facility_level, 0, 10) + clamp(cfg.staff_level, 0, 10)
    low = clamp(cfg.min_offer_count + (strength // 8), cfg.min_offer_count, cfg.max_offer_count)
    high = clamp(low + 2 + (strength // 10), low, cfg.max_offer_count)
    return random.randint(low, high)


def generate_slots(cfg: OfferGenerationConfig) -> List[Dict[str, object]]:
    """
    Generate limited sponsor slots with tier and rarity.
    """
    strength = clamp(cfg.facility_level, 0, 10) + clamp(cfg.staff_level, 0, 10)
    slot_count = clamp(1 + (strength // 4), 1, 8)
    rarity_weights = _slot_rarity_weights(strength)

    slots: List[Dict[str, object]] = []
    for index in range(slot_count):
        tier = random.choices(
            population=list(rarity_weights.keys()),
            weights=list(rarity_weights.values()),
            k=1,
        )[0]
        slots.append(
            {
                "slot_id": f"slot-{index + 1}",
                "slot_index": index + 1,
                "tier": tier,
                "occupied_contract_id": None,
            }
        )
    return slots


def generate_offer_batch(cfg: OfferGenerationConfig, count: int) -> List[Dict[str, object]]:
    return [generate_offer(cfg) for _ in range(count)]


def generate_offer(cfg: OfferGenerationConfig) -> Dict[str, object]:
    """
    Generate one sponsor offer with guaranteed and target components.
    """
    base_potential = random.randint(cfg.min_potential, cfg.max_potential)
    duration_years = random.choice([2, 3])
    guaranteed_type = random.choice(list(GUARANTEED_TYPE_MULTIPLIERS.keys()))
    guaranteed_share = round(random.uniform(cfg.min_guaranteed_share, cfg.max_guaranteed_share), 4)

    yearly_base_value = map_potential_to_yearly_base(base_potential, cfg)
    raw_total_value = yearly_base_value * duration_years
    multiplier = GUARANTEED_TYPE_MULTIPLIERS[guaranteed_type]
    adjusted_total_value = int(round(raw_total_value * multiplier))

    guaranteed_value = int(round(adjusted_total_value * guaranteed_share))
    target_pool_value = max(0, adjusted_total_value - guaranteed_value)

    targets = _generate_targets(
        target_pool_value=target_pool_value,
        min_count=cfg.min_targets_per_offer,
        max_count=cfg.max_targets_per_offer,
    )

    weekly_payout = int(round(guaranteed_value / (duration_years * WEEKS_PER_YEAR))) if guaranteed_type == "weekly" else 0

    return {
        "base_potential": base_potential,
        "duration_years": duration_years,
        "guaranteed_type": guaranteed_type,
        "guaranteed_type_label": GUARANTEED_TYPE_LABELS[guaranteed_type],
        "guaranteed_share": guaranteed_share,
        "yearly_base_value": yearly_base_value,
        "raw_total_value": raw_total_value,
        "type_multiplier": multiplier,
        "adjusted_total_value": adjusted_total_value,
        "guaranteed_value": guaranteed_value,
        "target_pool_value": target_pool_value,
        "weekly_guaranteed_payout": weekly_payout,
        "targets": targets,
        "diagnostics": {
            "base_potential": base_potential,
            "duration_years": duration_years,
            "yearly_base_value": yearly_base_value,
            "raw_total_value": raw_total_value,
            "guaranteed_type_multiplier": multiplier,
            "guaranteed_share": guaranteed_share,
            "adjusted_total_value": adjusted_total_value,
            "guaranteed_value": guaranteed_value,
            "target_pool_value": target_pool_value,
        },
    }


def apply_negotiation(
    offer: Dict[str, object], new_guaranteed_type: str
) -> Tuple[Dict[str, object], Dict[str, object]]:
    """
    Reprice guaranteed component for a new payout type and apply penalty.

    Target pool remains fixed from the original offer.
    """
    if new_guaranteed_type not in GUARANTEED_TYPE_MULTIPLIERS:
        raise ValueError(f"Unknown guaranteed type: {new_guaranteed_type}")

    duration_years = int(offer["duration_years"])
    raw_total_value = int(offer["raw_total_value"])
    guaranteed_share = float(offer["guaranteed_share"])
    target_pool_value = int(offer["target_pool_value"])

    new_multiplier = GUARANTEED_TYPE_MULTIPLIERS[new_guaranteed_type]
    new_adjusted_total = int(round(raw_total_value * new_multiplier))
    repriced_guaranteed = int(round(new_adjusted_total * guaranteed_share))
    negotiated_guaranteed = int(round(repriced_guaranteed * (1 - NEGOTIATION_PENALTY_RATE)))
    negotiated_total = negotiated_guaranteed + target_pool_value
    weekly_payout = (
        int(round(negotiated_guaranteed / (duration_years * WEEKS_PER_YEAR)))
        if new_guaranteed_type == "weekly"
        else 0
    )

    updated = dict(offer)
    updated.update(
        {
            "guaranteed_type": new_guaranteed_type,
            "guaranteed_type_label": GUARANTEED_TYPE_LABELS[new_guaranteed_type],
            "type_multiplier": new_multiplier,
            "adjusted_total_value": negotiated_total,
            "guaranteed_value": negotiated_guaranteed,
            "weekly_guaranteed_payout": weekly_payout,
            "negotiated": True,
            "negotiation_penalty_rate": NEGOTIATION_PENALTY_RATE,
        }
    )
    updated_diag = dict(updated.get("diagnostics", {}))
    updated_diag.update(
        {
            "negotiated_guaranteed_type": new_guaranteed_type,
            "negotiated_guaranteed_value": negotiated_guaranteed,
            "negotiated_total_value": negotiated_total,
            "negotiation_penalty_rate": NEGOTIATION_PENALTY_RATE,
        }
    )
    updated["diagnostics"] = updated_diag

    negotiation_meta = {
        "repriced_guaranteed_before_penalty": repriced_guaranteed,
        "negotiation_penalty_rate": NEGOTIATION_PENALTY_RATE,
    }
    return updated, negotiation_meta


def cancellation_quote(contract: Dict[str, object], current_week: int) -> Dict[str, object]:
    guaranteed_type = str(contract["guaranteed_type"])
    start_week = int(contract["start_week"])
    duration_years = int(contract["duration_years"])
    total_guaranteed = int(contract["guaranteed_value"])
    total_weeks = duration_years * WEEKS_PER_YEAR
    elapsed_weeks = max(0, current_week - start_week)
    remaining_weeks = max(0, total_weeks - elapsed_weeks)

    if guaranteed_type == "upfront":
        return {
            "cancellable": False,
            "cancel_fee": None,
            "reason": "Upfront guaranteed contracts cannot be cancelled.",
            "remaining_guaranteed_value": 0,
        }
    if guaranteed_type == "end_lump":
        return {
            "cancellable": True,
            "cancel_fee": 0,
            "reason": "End-of-contract lump sum contracts can be cancelled for free.",
            "remaining_guaranteed_value": total_guaranteed,
        }

    weekly_value = int(contract.get("weekly_guaranteed_payout", 0))
    remaining_guaranteed = weekly_value * remaining_weeks
    cancel_fee = int(round(remaining_guaranteed * WEEKLY_CANCEL_RATE))
    return {
        "cancellable": True,
        "cancel_fee": cancel_fee,
        "reason": "Weekly contracts require 10% of remaining guaranteed payouts.",
        "remaining_guaranteed_value": remaining_guaranteed,
    }


def _generate_targets(target_pool_value: int, min_count: int, max_count: int) -> List[Dict[str, object]]:
    max_allowed = min(max_count, len(TARGET_LIBRARY))
    min_allowed = clamp(min_count, 1, max_allowed)
    count = random.randint(min_allowed, max_allowed)
    selected = random.sample(TARGET_LIBRARY, k=count)
    total_weight = sum(float(target["weight"]) for target in selected)

    targets: List[Dict[str, object]] = []
    assigned = 0
    for index, target in enumerate(selected):
        weight = float(target["weight"])
        if index == count - 1:
            payout = max(0, target_pool_value - assigned)
        else:
            payout = int(round(target_pool_value * (weight / total_weight)))
            assigned += payout
        targets.append(
            {
                "code": target["code"],
                "label": target["label"],
                "weight": weight,
                "payout": payout,
            }
        )
    return targets


def _slot_rarity_weights(strength: int) -> Dict[str, int]:
    # Better facilities/staff increase higher-tier slot odds.
    if strength <= 6:
        return {"Bronze": 70, "Silver": 25, "Gold": 5, "Platinum": 0}
    if strength <= 12:
        return {"Bronze": 45, "Silver": 38, "Gold": 15, "Platinum": 2}
    if strength <= 16:
        return {"Bronze": 25, "Silver": 40, "Gold": 28, "Platinum": 7}
    return {"Bronze": 12, "Silver": 34, "Gold": 38, "Platinum": 16}
