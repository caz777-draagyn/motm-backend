"""
Match Engine Module

Simulates football matches using position-based matrices and attribute-driven evaluations.
"""

from .models import Player, Team
from .simulator import MatchSimulator, simulate_match
from .statistics import MatchStatsV2, aggregate_match_log_to_stats_v2

__all__ = [
    'Player',
    'Team',
    'MatchSimulator',
    'simulate_match',
    'MatchStatsV2',
    'aggregate_match_log_to_stats_v2',
]
