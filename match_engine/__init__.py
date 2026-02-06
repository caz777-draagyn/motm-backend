"""
Match Engine Module

Simulates football matches using position-based matrices and attribute-driven evaluations.
"""

from .models import Player, Team
from .simulator import MatchSimulator, simulate_match
from .statistics import MatchStatsV2, aggregate_match_log_to_stats_v2
from .formations import (
    calculate_formation_characteristics,
    FORMATION_CHARACTERISTICS,
    POSITION_ALLOCATION_MATRIX,
    SHIFTING_CAPACITY_MATRIX
)

__all__ = [
    'Player',
    'Team',
    'MatchSimulator',
    'simulate_match',
    'MatchStatsV2',
    'aggregate_match_log_to_stats_v2',
    'calculate_formation_characteristics',
    'FORMATION_CHARACTERISTICS',
    'POSITION_ALLOCATION_MATRIX',
    'SHIFTING_CAPACITY_MATRIX',
]
