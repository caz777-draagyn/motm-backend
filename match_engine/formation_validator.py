"""
Formation validation rules for team setups.
"""

from typing import List, Dict
from .models import Team, Player


def validate_formation(team: Team):
    """
    Validate a team's formation against the rules.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Count players by position
    position_count = {}
    for player in team.players:
        pos = player.matrix_position
        position_count[pos] = position_count.get(pos, 0) + 1
    
    # Rule 1: Must have exactly 1 GK
    gk_count = position_count.get("GK", 0)
    if gk_count != 1:
        errors.append(f"Must have exactly 1 GK, found {gk_count}")
    
    # Rule 2: Must have 1-3 DC
    dc_count = position_count.get("DC", 0)
    if dc_count < 1 or dc_count > 3:
        errors.append(f"Must have 1-3 DC, found {dc_count}")
    
    # Rule 3: Must have 1-3 total central midfielders (DMC + MC + OMC)
    central_mid_count = (
        position_count.get("DMC", 0) +
        position_count.get("MC", 0) +
        position_count.get("OMC", 0)
    )
    if central_mid_count < 1 or central_mid_count > 3:
        errors.append(f"Must have 1-3 central midfielders (DMC + MC + OMC), found {central_mid_count}")
    
    # Rule 4: Must have at least 1 wide player on each side
    left_wide = (
        position_count.get("DL", 0) +
        position_count.get("DML", 0) +
        position_count.get("ML", 0) +
        position_count.get("OML", 0)
    )
    right_wide = (
        position_count.get("DR", 0) +
        position_count.get("DMR", 0) +
        position_count.get("MR", 0) +
        position_count.get("OMR", 0)
    )
    
    if left_wide < 1:
        errors.append("Must have at least 1 left wide player (DL, DML, ML, or OML)")
    if right_wide < 1:
        errors.append("Must have at least 1 right wide player (DR, DMR, MR, or OMR)")
    
    # Rule 5: Cannot have both DL and DML
    if position_count.get("DL", 0) > 0 and position_count.get("DML", 0) > 0:
        errors.append("Cannot have both DL and DML (choose one left defensive position)")
    
    # Rule 6: Cannot have both DR and DMR
    if position_count.get("DR", 0) > 0 and position_count.get("DMR", 0) > 0:
        errors.append("Cannot have both DR and DMR (choose one right defensive position)")
    
    # Rule 7: Cannot have both ML and OML
    if position_count.get("ML", 0) > 0 and position_count.get("OML", 0) > 0:
        errors.append("Cannot have both ML and OML (choose one left midfield position)")
    
    # Rule 8: Cannot have both MR and OMR
    if position_count.get("MR", 0) > 0 and position_count.get("OMR", 0) > 0:
        errors.append("Cannot have both MR and OMR (choose one right midfield position)")
    
    # Rule 9: Each wide position can only appear once
    wide_positions = ["DL", "DR", "DML", "DMR", "ML", "MR", "OML", "OMR"]
    for pos in wide_positions:
        count = position_count.get(pos, 0)
        if count > 1:
            errors.append(f"Cannot have {count} players at {pos} (each wide position can only appear once)")
    
    return len(errors) == 0, errors


def get_formation_summary(team: Team) -> Dict[str, int]:
    """Get a summary of the formation for display."""
    position_count = {}
    for player in team.players:
        pos = player.matrix_position
        position_count[pos] = position_count.get(pos, 0) + 1
    
    return {
        "GK": position_count.get("GK", 0),
        "DC": position_count.get("DC", 0),
        "DL": position_count.get("DL", 0),
        "DR": position_count.get("DR", 0),
        "DML": position_count.get("DML", 0),
        "DMC": position_count.get("DMC", 0),
        "DMR": position_count.get("DMR", 0),
        "ML": position_count.get("ML", 0),
        "MC": position_count.get("MC", 0),
        "MR": position_count.get("MR", 0),
        "OML": position_count.get("OML", 0),
        "OMC": position_count.get("OMC", 0),
        "OMR": position_count.get("OMR", 0),
        "FC": position_count.get("FC", 0),
    }
