"""
Formation characteristics calculation for match engine.
Analyzes team formations to determine tactical characteristics.
"""

from typing import Dict
from .models import Team
from .constants import POSITIONS

# Position Allocation (PA) Matrix
# Each position contributes differently to the 5 characteristics
POSITION_ALLOCATION_MATRIX = {
    # Position: {Possession, Attack_Center, Attack_Wide, Defend_Center, Defend_Wide}
    "GK": {
        "Possession": 0.0,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.0,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.0
    },
    "DL": {
        "Possession": 0.4,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.2,
        "Defend_Wide": 1.0
    },
    "DC": {
        "Possession": 0.3,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.0,
        "Defend_Center": 1.0,
        "Defend_Wide": 0.3
    },
    "DR": {
        "Possession": 0.4,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.2,
        "Defend_Wide": 1.0
    },
    "DML": {
        "Possession": 0.6,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.6,
        "Defend_Center": 0.1,
        "Defend_Wide": 0.8
    },
    "DMC": {
        "Possession": 0.9,
        "Attack_Center": 0.3,
        "Attack_Wide": 0.0,
        "Defend_Center": 0.7,
        "Defend_Wide": 0.2
    },
    "DMR": {
        "Possession": 0.6,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.6,
        "Defend_Center": 0.1,
        "Defend_Wide": 0.8
    },
    "ML": {
        "Possession": 0.5,
        "Attack_Center": 0.1,
        "Attack_Wide": 0.8,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.7
    },
    "MC": {
        "Possession": 1.0,
        "Attack_Center": 0.6,
        "Attack_Wide": 0.1,
        "Defend_Center": 0.4,
        "Defend_Wide": 0.1
    },
    "MR": {
        "Possession": 0.5,
        "Attack_Center": 0.1,
        "Attack_Wide": 0.8,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.7
    },
    "OML": {
        "Possession": 0.3,
        "Attack_Center": 0.2,
        "Attack_Wide": 1.0,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.3
    },
    "OMC": {
        "Possession": 0.7,
        "Attack_Center": 0.9,
        "Attack_Wide": 0.2,
        "Defend_Center": 0.1,
        "Defend_Wide": 0.0
    },
    "OMR": {
        "Possession": 0.3,
        "Attack_Center": 0.2,
        "Attack_Wide": 1.0,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.3
    },
    "FC": {
        "Possession": 0.1,
        "Attack_Center": 1.0,
        "Attack_Wide": 0.1,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.0
    }
}

# Shifting Capacity (SC) Matrix
# Same structure as PA matrix
SHIFTING_CAPACITY_MATRIX = {
    # Position: {Possession, Attack_Center, Attack_Wide, Defend_Center, Defend_Wide}
    "GK": {
        "Possession": 0.0,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.0,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.0
    },
    "DL": {
        "Possession": 0.1,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.3,
        "Defend_Center": 0.2,
        "Defend_Wide": 0.4
    },
    "DC": {
        "Possession": 0.1,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.1,
        "Defend_Center": 0.2,
        "Defend_Wide": 0.2
    },
    "DR": {
        "Possession": 0.1,
        "Attack_Center": 0.0,
        "Attack_Wide": 0.3,
        "Defend_Center": 0.2,
        "Defend_Wide": 0.4
    },
    "DML": {
        "Possession": 0.3,
        "Attack_Center": 0.1,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.2,
        "Defend_Wide": 0.3
    },
    "DMC": {
        "Possession": 0.5,
        "Attack_Center": 0.2,
        "Attack_Wide": 0.0,
        "Defend_Center": 0.2,
        "Defend_Wide": 0.2
    },
    "DMR": {
        "Possession": 0.3,
        "Attack_Center": 0.1,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.2,
        "Defend_Wide": 0.3
    },
    "ML": {
        "Possession": 0.0,
        "Attack_Center": 0.1,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.3
    },
    "MC": {
        "Possession": 0.4,
        "Attack_Center": 0.4,
        "Attack_Wide": 0.1,
        "Defend_Center": 0.3,
        "Defend_Wide": 0.1
    },
    "MR": {
        "Possession": 0.0,
        "Attack_Center": 0.1,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.3
    },
    "OML": {
        "Possession": 0.0,
        "Attack_Center": 0.3,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.0
    },
    "OMC": {
        "Possession": 0.2,
        "Attack_Center": 0.4,
        "Attack_Wide": 0.1,
        "Defend_Center": 0.1,
        "Defend_Wide": 0.0
    },
    "OMR": {
        "Possession": 0.0,
        "Attack_Center": 0.3,
        "Attack_Wide": 0.4,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.0
    },
    "FC": {
        "Possession": 0.0,
        "Attack_Center": 0.3,
        "Attack_Wide": 0.3,
        "Defend_Center": 0.0,
        "Defend_Wide": 0.1
    }
}

# List of all characteristics
FORMATION_CHARACTERISTICS = [
    "Possession",
    "Attack_Center",
    "Attack_Wide",
    "Defend_Center",
    "Defend_Wide"
]


def _calculate_structural_depth_central(position_count: Dict[str, int]) -> float:
    """
    Calculate Structural Depth (SD) for central characteristics.
    
    Counts central midfielder layers (DMC, MC, OMC) and applies:
    - 0.2 (1 layer), 0.6 (2 layers), 1.0 (3 layers)
    - Bonus: +0.1 per layer that has exactly 2 players (can happen once per layer)
    """
    # Count layers and players in each layer
    dmc_count = position_count.get("DMC", 0)
    mc_count = position_count.get("MC", 0)
    omc_count = position_count.get("OMC", 0)
    
    # Count number of layers (presence of each type)
    num_layers = 0
    if dmc_count > 0:
        num_layers += 1
    if mc_count > 0:
        num_layers += 1
    if omc_count > 0:
        num_layers += 1
    
    # Base SD value based on number of layers
    if num_layers == 1:
        sd = 0.2
    elif num_layers == 2:
        sd = 0.6
    elif num_layers == 3:
        sd = 1.0
    else:
        sd = 0.0
    
    # Bonus: +0.1 per layer that has exactly 2 players (can happen once per layer)
    if dmc_count == 2:
        sd += 0.1
    if mc_count == 2:
        sd += 0.1
    if omc_count == 2:
        sd += 0.1
    
    return sd


def _calculate_structural_depth_wide(position_count: Dict[str, int]) -> float:
    """
    Calculate Structural Depth (SD) for wide characteristics.
    
    Counts players on left side (DL, DML, ML, OML) and right side (DR, DMR, MR, OMR).
    For each side: 0 (0 players), 0.4 (1 player), 1.0 (2 players)
    SD = average of left and right side values
    """
    # Count left side players
    left_side = (
        position_count.get("DL", 0) +
        position_count.get("DML", 0) +
        position_count.get("ML", 0) +
        position_count.get("OML", 0)
    )
    
    # Count right side players
    right_side = (
        position_count.get("DR", 0) +
        position_count.get("DMR", 0) +
        position_count.get("MR", 0) +
        position_count.get("OMR", 0)
    )
    
    # Calculate value for each side
    if left_side == 0:
        left_value = 0.0
    elif left_side == 1:
        left_value = 0.4
    elif left_side == 2:
        left_value = 1.0
    else:
        # Cap at 1.0 for 2+ players (formations with more than 2 per side not allowed)
        left_value = 1.0
    
    if right_side == 0:
        right_value = 0.0
    elif right_side == 1:
        right_value = 0.4
    elif right_side == 2:
        right_value = 1.0
    else:
        # Cap at 1.0 for 2+ players (formations with more than 2 per side not allowed)
        right_value = 1.0
    
    # SD is average of left and right
    return (left_value + right_value) / 2.0


def calculate_formation_characteristics(team: Team) -> Dict[str, float]:
    """
    Calculate the 5 formation characteristics for a team.
    
    Each characteristic is calculated as: X = PA + SD + SC
    - PA (Position Allocation): weighted sum of players in each position
    - SD (Structural Depth): bonus based on vertical layers
    - SC (Shifting Capacity): weighted sum of players in each position
    
    Args:
        team: Team object with players
        
    Returns:
        Dictionary mapping characteristic name to calculated value
        {
            "Possession": float,
            "Attack_Center": float,
            "Attack_Wide": float,
            "Defend_Center": float,
            "Defend_Wide": float
        }
    """
    # Count players by position
    position_count = {}
    for player in team.players:
        pos = player.matrix_position
        position_count[pos] = position_count.get(pos, 0) + 1
    
    # Initialize characteristics
    characteristics = {}
    
    # Calculate PA, SD, and SC for each characteristic
    for char in FORMATION_CHARACTERISTICS:
        # Calculate PA (Position Allocation)
        pa = 0.0
        for position, count in position_count.items():
            weight = POSITION_ALLOCATION_MATRIX.get(position, {}).get(char, 0.0)
            pa += count * weight
        
        # Calculate SD (Structural Depth)
        if char in ["Possession", "Attack_Center", "Defend_Center"]:
            sd = _calculate_structural_depth_central(position_count)
        else:  # Attack_Wide, Defend_Wide
            sd = _calculate_structural_depth_wide(position_count)
        
        # Calculate SC (Shifting Capacity)
        sc = 0.0
        for position, count in position_count.items():
            weight = SHIFTING_CAPACITY_MATRIX.get(position, {}).get(char, 0.0)
            sc += count * weight
        
        # Final value: X = PA + SD + SC
        characteristics[char] = pa + sd + sc
    
    return characteristics
