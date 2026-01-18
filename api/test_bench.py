"""
API endpoints for test bench UI.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict
from match_engine.models import Player, Team
from match_engine.simulator import simulate_match
from match_engine.statistics import aggregate_match_log_to_stats_v2
from api.match_engine import (
    PlayerInput, TeamInput, player_input_to_model, team_input_to_model,
    skill_usage_to_response, TeamStatsResponse, PlayerStatsResponse
)

router = APIRouter(prefix="/api/test-bench", tags=["test-bench"])


class BatchSimulationRequest(BaseModel):
    """Request to simulate multiple matches."""
    home_team: TeamInput
    away_team: TeamInput
    num_matches: int = Field(default=1, ge=1, le=10000, description="Number of matches to simulate")
    minutes: int = Field(default=90, ge=1, le=120)


class BatchSimulationResponse(BaseModel):
    """Response from batch simulation."""
    num_matches: int
    home_wins: int
    away_wins: int
    draws: int
    home_avg_goals: float
    away_avg_goals: float
    aggregated_stats: Dict  # Will contain team and player stats


@router.get("/", response_class=HTMLResponse)
async def test_bench_ui():
    """Serve the test bench UI."""
    try:
        with open("templates/test_bench.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Test Bench UI not found</h1><p>Please create templates/test_bench.html</p>",
            status_code=404
        )


@router.post("/simulate", response_model=BatchSimulationResponse)
async def batch_simulate(request: BatchSimulationRequest):
    """
    Simulate multiple matches between two teams and return aggregated statistics.
    """
    try:
        # Convert input to models
        home_team = team_input_to_model(request.home_team)
        away_team = team_input_to_model(request.away_team)
        
        # Validate formations
        from match_engine.formation_validator import validate_formation
        home_valid, home_errors = validate_formation(home_team)
        away_valid, away_errors = validate_formation(away_team)
        
        if not home_valid or not away_valid:
            error_messages = []
            if not home_valid:
                error_messages.append(f"Home team formation invalid: {'; '.join(home_errors)}")
            if not away_valid:
                error_messages.append(f"Away team formation invalid: {'; '.join(away_errors)}")
            raise ValueError("; ".join(error_messages))
        
        # Run simulations
        from collections import Counter
        all_stats = []
        home_wins = 0
        away_wins = 0
        draws = 0
        total_home_goals = 0
        total_away_goals = 0
        match_score_frequency = Counter()  # Track match scores separately
        
        for _ in range(request.num_matches):
            sim = simulate_match(home_team, away_team, minutes=request.minutes)
            stats = aggregate_match_log_to_stats_v2(sim)
            all_stats.append(stats)
            
            home_score = stats.team[home_team.name].shooting.goals
            away_score = stats.team[away_team.name].shooting.goals
            
            total_home_goals += home_score
            total_away_goals += away_score
            
            # Track result frequency
            if home_score > away_score:
                home_wins += 1
                stats.team[home_team.name].result_frequency["win"] += 1
                stats.team[away_team.name].result_frequency["loss"] += 1
            elif away_score > home_score:
                away_wins += 1
                stats.team[away_team.name].result_frequency["win"] += 1
                stats.team[home_team.name].result_frequency["loss"] += 1
            else:
                draws += 1
                stats.team[home_team.name].result_frequency["draw"] += 1
                stats.team[away_team.name].result_frequency["draw"] += 1
            
            # Track score frequency (format: "home-away")
            score_key = f"{home_score}-{away_score}"
            match_score_frequency[score_key] += 1
        
        # Aggregate all statistics
        aggregated = all_stats[0]
        for stats in all_stats[1:]:
            aggregated.merge(stats)
        
        # Build response
        home_team_stats = aggregated.team[home_team.name]
        away_team_stats = aggregated.team[away_team.name]
        
        player_stats_list = []
        for (team_name, player_name), player_stats in aggregated.player.items():
            # Format name as position_name
            display_name = f"{player_stats.position}_{player_stats.name}" if player_stats.position else player_stats.name
            player_stats_list.append({
                "name": display_name,
                "position": player_stats.position,
                "original_name": player_stats.name,
                "team": player_stats.team,
                "goals": player_stats.goals,
                "assists": player_stats.assists,
                "shots": player_stats.shots,
                "shots_on": player_stats.shots_on,
                "creator_attempts": player_stats.creator_off.attempts,
                "creator_successes": player_stats.creator_off.successes,
                "finisher_attempts": player_stats.finisher_off.attempts,
                "finisher_successes": player_stats.finisher_off.successes,
                # Detailed creator stats by type
                "creator_attempts_by_type": dict(player_stats.creator_off.attempt_by_type),
                "creator_successes_by_type": dict(player_stats.creator_off.success_by_type),
                # Detailed finisher stats by type
                "finisher_attempts_by_type": dict(player_stats.finisher_off.attempt_by_type),
                "finisher_successes_by_type": dict(player_stats.finisher_off.success_by_type),
                # Shooting by type
                "shots_by_type": dict(player_stats.shooting.shots_by_type),
                "shots_on_by_type": dict(player_stats.shooting.shots_on_by_type),
                "goals_by_type": dict(player_stats.shooting.goals_by_type),
                # Assists by chance type
                "assists_by_chance_type": dict(player_stats.assists_by_chance_type),
                # Goalkeeper stats (only populated for GKs)
                "goalkeeper_stats": {
                    "intercept_attempts_by_type": dict(player_stats.goalkeeper_stats.intercept_attempts_by_type),
                    "intercept_successes_by_type": dict(player_stats.goalkeeper_stats.intercept_successes_by_type),
                    "shots_conceded_by_type": dict(player_stats.goalkeeper_stats.shots_conceded_by_type),
                    "shots_on_target_by_type": dict(player_stats.goalkeeper_stats.shots_on_target_by_type),
                    "saves_by_type": dict(player_stats.goalkeeper_stats.saves_by_type),
                },
                "skill_usage": skill_usage_to_response(player_stats.skill_usage).dict()
            })
        
        # Sort players by position (defensive to offensive)
        from match_engine.position_order import get_position_order
        player_stats_list.sort(key=lambda p: (get_position_order(p.get("position", "")), p["name"]))
        
        return BatchSimulationResponse(
            num_matches=request.num_matches,
            home_wins=home_wins,
            away_wins=away_wins,
            draws=draws,
            home_avg_goals=total_home_goals / request.num_matches,
            away_avg_goals=total_away_goals / request.num_matches,
            aggregated_stats={
                "match_score_frequency": dict(match_score_frequency),
                "home_team": {
                    "name": home_team_stats.name,
                    "goals": home_team_stats.shooting.goals,
                    "shots": home_team_stats.shooting.shots,
                    "shots_on": home_team_stats.shooting.shots_on,
                    "creator_attempts": home_team_stats.creator_off.attempts,
                    "creator_successes": home_team_stats.creator_off.successes,
                    "finisher_attempts": home_team_stats.finisher_off.attempts,
                    "finisher_successes": home_team_stats.finisher_off.successes,
                    "result_frequency": dict(home_team_stats.result_frequency),
                    "score_frequency": dict(home_team_stats.score_frequency),
                    "skill_usage": skill_usage_to_response(home_team_stats.skill_usage).dict()
                },
                "away_team": {
                    "name": away_team_stats.name,
                    "goals": away_team_stats.shooting.goals,
                    "shots": away_team_stats.shooting.shots,
                    "shots_on": away_team_stats.shooting.shots_on,
                    "creator_attempts": away_team_stats.creator_off.attempts,
                    "creator_successes": away_team_stats.creator_off.successes,
                    "finisher_attempts": away_team_stats.finisher_off.attempts,
                    "finisher_successes": away_team_stats.finisher_off.successes,
                    "result_frequency": dict(away_team_stats.result_frequency),
                    "score_frequency": dict(away_team_stats.score_frequency),
                    "skill_usage": skill_usage_to_response(away_team_stats.skill_usage).dict()
                },
                "players": player_stats_list
            }
        )
    
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
