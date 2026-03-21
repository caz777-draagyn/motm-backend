"""
Position ordering for sorting players from defensive to offensive.
"""

# Position order: defensive to offensive
POSITION_ORDER = {
    "GK": 0,
    "DL": 1, "DC": 2, "DR": 3,
    "DML": 4, "DMC": 5, "DMR": 6,
    "ML": 7, "MC": 8, "MR": 9,
    "OML": 10, "OMC": 11, "OMR": 12,
    "FC": 13,
}

def get_position_order(position: str) -> int:
    """Get sort order for a position (lower = more defensive)."""
    return POSITION_ORDER.get(position, 99)
