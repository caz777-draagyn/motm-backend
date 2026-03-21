"""
API endpoints for match engine simulation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from match_engine.models import Player, Team
from match_engine.simulator import simulate_match
from match_engine.statistics import aggregate_match_log_to_stats_v2
from match_engine.constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS, POSITIONS

router = APIRouter(prefix="/api/match-engine", tags=["match-engine"])


# ============ REQUEST/RESPONSE MODELS ============

class PlayerInput(BaseModel):
    """Player input for match simulation."""
    name: str
    position: str = Field(..., description="Position code (GK, DL, DC, etc.)")
    attributes: Dict[str, int] = Field(..., description="Attribute name -> value mapping")
    is_goalkeeper: bool = False


class TeamInput(BaseModel):
    """Team input for match simulation."""
    name: str
    players: List[PlayerInput] = Field(..., min_length=11, max_length=11)


class MatchSimulationRequest(BaseModel):
    """Request to simulate a match."""
    home_team: TeamInput
    away_team: TeamInput
    minutes: int = Field(default=90, ge=1, le=120, description="Match length in minutes")


class SkillUsageResponse(BaseModel):
    """Skill usage statistics."""
    total_usage: Dict[str, int] = Field(..., description="Total times each skill was used")
    usage_by_event: Dict[str, Dict[str, int]] = Field(..., description="Skill -> Event Type -> Count")


class PlayerStatsResponse(BaseModel):
    """Player statistics response."""
    name: str
    team: str
    goals: int
    assists: int
    shots: int
    shots_on: int
    creator_attempts: int
    creator_successes: int
    finisher_attempts: int
    finisher_successes: int
    skill_usage: SkillUsageResponse


class TeamStatsResponse(BaseModel):
    """Team statistics response."""
    name: str
    goals: int
    shots: int
    shots_on: int
    creator_attempts: int
    creator_successes: int
    finisher_attempts: int
    finisher_successes: int
    skill_usage: SkillUsageResponse


class MatchResultResponse(BaseModel):
    """Match simulation result."""
    home_score: int
    away_score: int
    match_length: int
    total_events: int
    home_team_stats: TeamStatsResponse
    away_team_stats: TeamStatsResponse
    player_stats: List[PlayerStatsResponse]


# ============ HELPER FUNCTIONS ============

def player_input_to_model(player_input: PlayerInput) -> Player:
    """Convert PlayerInput to Player model."""
    return Player(
        name=player_input.name,
        matrix_position=player_input.position,
        attributes=player_input.attributes,
        is_goalkeeper=player_input.is_goalkeeper
    )


def team_input_to_model(team_input: TeamInput) -> Team:
    """Convert TeamInput to Team model."""
    players = [player_input_to_model(p) for p in team_input.players]
    return Team(name=team_input.name, players=players)


def skill_usage_to_response(skill_usage) -> SkillUsageResponse:
    """Convert SkillUsage to response format."""
    return SkillUsageResponse(
        total_usage=dict(skill_usage.total_usage),
        usage_by_event={
            skill: dict(event_counts)
            for skill, event_counts in skill_usage.usage_by_event.items()
        }
    )


# ============ API ENDPOINTS ============

@router.post("/simulate", response_model=MatchResultResponse)
async def simulate_match_endpoint(request: MatchSimulationRequest):
    """
    Simulate a single match between two teams.
    
    Returns detailed statistics including team stats, player stats, and skill usage.
    """
    try:
        # Convert input to models
        home_team = team_input_to_model(request.home_team)
        away_team = team_input_to_model(request.away_team)
        
        # Run simulation
        sim = simulate_match(home_team, away_team, minutes=request.minutes)
        
        # Aggregate statistics
        stats = aggregate_match_log_to_stats_v2(sim)
        
        # Calculate scores
        home_score = stats.team[home_team.name].shooting.goals
        away_score = stats.team[away_team.name].shooting.goals
        
        # Build response
        home_team_stats = stats.team[home_team.name]
        away_team_stats = stats.team[away_team.name]
        
        player_stats_list = []
        for (team_name, player_name), player_stats in stats.player.items():
            player_stats_list.append(PlayerStatsResponse(
                name=player_stats.name,
                team=player_stats.team,
                goals=player_stats.goals,
                assists=player_stats.assists,
                shots=player_stats.shots,
                shots_on=player_stats.shots_on,
                creator_attempts=player_stats.creator_off.attempts,
                creator_successes=player_stats.creator_off.successes,
                finisher_attempts=player_stats.finisher_off.attempts,
                finisher_successes=player_stats.finisher_off.successes,
                skill_usage=skill_usage_to_response(player_stats.skill_usage)
            ))
        
        return MatchResultResponse(
            home_score=home_score,
            away_score=away_score,
            match_length=sim.minutes,
            total_events=len(sim.log),
            home_team_stats=TeamStatsResponse(
                name=home_team_stats.name,
                goals=home_team_stats.shooting.goals,
                shots=home_team_stats.shooting.shots,
                shots_on=home_team_stats.shooting.shots_on,
                creator_attempts=home_team_stats.creator_off.attempts,
                creator_successes=home_team_stats.creator_off.successes,
                finisher_attempts=home_team_stats.finisher_off.attempts,
                finisher_successes=home_team_stats.finisher_off.successes,
                skill_usage=skill_usage_to_response(home_team_stats.skill_usage)
            ),
            away_team_stats=TeamStatsResponse(
                name=away_team_stats.name,
                goals=away_team_stats.shooting.goals,
                shots=away_team_stats.shooting.shots,
                shots_on=away_team_stats.shooting.shots_on,
                creator_attempts=away_team_stats.creator_off.attempts,
                creator_successes=away_team_stats.creator_off.successes,
                finisher_attempts=away_team_stats.finisher_off.attempts,
                finisher_successes=away_team_stats.finisher_off.successes,
                skill_usage=skill_usage_to_response(away_team_stats.skill_usage)
            ),
            player_stats=player_stats_list
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/constants")
async def get_constants():
    """Get available constants (positions, attributes, etc.) for the match engine."""
    return {
        "positions": POSITIONS,
        "outfield_attributes": OUTFIELD_ATTRS,
        "goalkeeper_attributes": GOALKEEPER_ATTRS
    }
