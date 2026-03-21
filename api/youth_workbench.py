"""
API endpoints for youth player workbench UI.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from utils.player_generation import create_player_data
from utils.player_development import compile_growth_schedule, train_one_season_with_growth
import uuid

router = APIRouter(prefix="/api/youth-workbench", tags=["youth-workbench"])


class GeneratePlayersRequest(BaseModel):
    """Request to generate multiple players for analysis."""
    youth_facilities: int = Field(default=5, ge=0, le=10)
    num_players: int = Field(default=100, ge=1, le=10000)
    is_goalkeeper: bool = False


class GeneratePlayersResponse(BaseModel):
    """Response from player generation."""
    players: List[Dict]
    statistics: Dict


class DevelopPlayersRequest(BaseModel):
    """Request to develop players from age 16y1."""
    youth_facilities: int = Field(default=5, ge=0, le=10)
    training_facilities: int = Field(default=5, ge=0, le=10)
    num_players: int = Field(default=10, ge=1, le=50)
    is_goalkeeper: bool = False
    primary_program: Optional[str] = "Balanced"
    primary_share: float = Field(default=0.4, ge=0, le=1)
    secondary_program: Optional[str] = "Balanced"
    secondary_share: float = Field(default=0.2, ge=0, le=1)
    general_share: float = Field(default=0.4, ge=0, le=1)
    years_to_simulate: int = Field(default=16, ge=1, le=20)
    min_potential: int = Field(default=200, ge=200, le=3000)
    max_potential: int = Field(default=3000, ge=200, le=3000)
    use_potential_range: bool = Field(default=False, description="If True, generate potential uniformly within range instead of using youth facilities")


class DevelopPlayersResponse(BaseModel):
    """Response from player development."""
    players: List[Dict]  # List of player snapshots per year
    development_points: List[Dict]  # DP breakdown per year


@router.get("/", response_class=HTMLResponse)
async def youth_workbench_ui():
    """Serve the youth workbench UI."""
    try:
        with open("templates/youth_workbench.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Youth Workbench UI not found</h1><p>Please create templates/youth_workbench.html</p>",
            status_code=404
        )


@router.post("/generate", response_model=GeneratePlayersResponse)
async def generate_players(request: GeneratePlayersRequest):
    """
    Generate multiple players for analysis.
    Returns player data and statistics for histogram generation.
    """
    players = []
    
    for _ in range(request.num_players):
        player_data = create_player_data(
            club_id=str(uuid.uuid4()),
            youth_facilities=request.youth_facilities,
            is_goalkeeper=request.is_goalkeeper,
            youth_player=False
        )
        players.append(player_data)
    
    # Calculate statistics
    potentials = [p["potential"] for p in players]
    birth_dev_pcts = [p["birth_dev_pct"] for p in players]
    base_training_pcts = [p["base_training_pct"] for p in players]
    growth_training_pcts = [p["growth_training_pct"] for p in players]
    growth_shapes = [p["growth_shape"] for p in players]  # This is now the k parameter
    growth_peak_ages = [p["growth_peak_age"] for p in players]  # This is the b parameter
    
    statistics = {
        "potential": {
            "min": min(potentials),
            "max": max(potentials),
            "mean": sum(potentials) / len(potentials),
            "values": potentials
        },
        "birth_dev_pct": {
            "min": min(birth_dev_pcts),
            "max": max(birth_dev_pcts),
            "mean": sum(birth_dev_pcts) / len(birth_dev_pcts),
            "values": birth_dev_pcts
        },
        "base_training_pct": {
            "min": min(base_training_pcts),
            "max": max(base_training_pcts),
            "mean": sum(base_training_pcts) / len(base_training_pcts),
            "values": base_training_pcts
        },
        "growth_training_pct": {
            "min": min(growth_training_pcts),
            "max": max(growth_training_pcts),
            "mean": sum(growth_training_pcts) / len(growth_training_pcts),
            "values": growth_training_pcts
        },
        "growth_shape": {  # k parameter (1.1-3.0, controls width)
            "min": min(growth_shapes),
            "max": max(growth_shapes),
            "mean": sum(growth_shapes) / len(growth_shapes),
            "values": growth_shapes
        },
        "growth_peak_age": {  # b parameter (1.0-10.0, peak age in years)
            "min": min(growth_peak_ages),
            "max": max(growth_peak_ages),
            "mean": sum(growth_peak_ages) / len(growth_peak_ages),
            "values": growth_peak_ages
        }
    }
    
    return GeneratePlayersResponse(players=players, statistics=statistics)


@router.post("/develop", response_model=DevelopPlayersResponse)
async def develop_players(request: DevelopPlayersRequest):
    """
    Create players at age 16y1 and simulate their development over multiple years.
    Returns yearly snapshots of player attributes and development points.
    """
    # Create 10 players at 16y1 (16 years, 1 month = 193 months, training_weeks = 1)
    import random
    import os
    
    # Get available profile pictures (PP3Anglosphere####.png format)
    profile_pics_dir = "gfx/Anglosphere"
    available_pics = []
    if os.path.exists(profile_pics_dir):
        for filename in os.listdir(profile_pics_dir):
            if filename.startswith("PP3Anglosphere") and filename.endswith(".png"):
                # Extract number from filename
                try:
                    num_str = filename.replace("PP3Anglosphere", "").replace(".png", "")
                    num = int(num_str)
                    available_pics.append((num, filename))
                except ValueError:
                    continue
        available_pics.sort()
    
    # If no pics found, use empty list (will result in no image)
    pic_numbers = [pic[0] for pic in available_pics] if available_pics else []
    
    players_data = []
    
    if request.use_potential_range:
        # Generate potential directly within range (uniform distribution)
        for _ in range(request.num_players):
            # Generate potential uniformly in the specified range
            potential = random.randint(request.min_potential, request.max_potential)
            
            # Create player data, then override potential
            player_data = create_player_data(
                club_id=str(uuid.uuid4()),
                youth_facilities=request.youth_facilities,  # Still used for other generation aspects
                is_goalkeeper=request.is_goalkeeper,
                youth_player=False
            )
            # Override potential with the directly generated value
            player_data["potential"] = potential
            
            # Set to 16y1 (193 months, 1 training week)
            player_data["actual_age_months"] = 16 * 12 + 1
            player_data["training_age_weeks"] = 1
            
            # Assign random profile picture
            if pic_numbers:
                pic_num = random.choice(pic_numbers)
                player_data["profile_pic"] = f"PP3Anglosphere{pic_num:04d}.png"
            else:
                player_data["profile_pic"] = None
            
            players_data.append(player_data)
    else:
        # Filter by potential range using youth facilities distribution
        max_attempts = request.num_players * 50
        attempts = 0
        
        while len(players_data) < request.num_players and attempts < max_attempts:
            attempts += 1
            player_data = create_player_data(
                club_id=str(uuid.uuid4()),
                youth_facilities=request.youth_facilities,
                is_goalkeeper=request.is_goalkeeper,
                youth_player=False
            )
        # Filter by potential
        if request.min_potential <= player_data["potential"] <= request.max_potential:
            # Set to 16y1 (193 months, 1 training week)
            player_data["actual_age_months"] = 16 * 12 + 1
            player_data["training_age_weeks"] = 1
            
            # Assign random profile picture
            if pic_numbers:
                pic_num = random.choice(pic_numbers)
                player_data["profile_pic"] = f"PP3Anglosphere{pic_num:04d}.png"
            else:
                player_data["profile_pic"] = None
            
            players_data.append(player_data)
        
        # Validate we have at least some players
        if len(players_data) == 0:
            raise ValueError(
                f"Could not generate any players with potential range {request.min_potential}-{request.max_potential}. "
                f"Try widening the potential range, adjusting youth facilities level, or enable 'Use Potential Range Directly'."
            )
        
        # If we have fewer than requested, log a warning but continue with what we have
        if len(players_data) < request.num_players:
            import logging
            logging.warning(
                f"Only generated {len(players_data)} out of {request.num_players} requested players "
                f"within potential range {request.min_potential}-{request.max_potential} after {attempts} attempts. "
                f"Consider enabling 'Use Potential Range Directly' for guaranteed results."
            )
    
    # Simple player class for development functions
    class SimplePlayer:
        def __init__(self, data):
            self.id = uuid.uuid4()
            self.potential = data["potential"]
            self.birth_dev_pct = data["birth_dev_pct"]
            self.base_training_pct = data["base_training_pct"]
            self.growth_training_pct = data["growth_training_pct"]
            self.growth_shape = data["growth_shape"]  # k parameter
            self.growth_peak_age = data["growth_peak_age"]  # b parameter
            self.attributes = data["attributes"].copy()
            self.actual_age_months = data["actual_age_months"]
            self.training_age_weeks = data["training_age_weeks"]
            self.is_goalkeeper = data["is_goalkeeper"]
            self.name = data["name"]
            self.profile_pic = data.get("profile_pic")
    
    players = [SimplePlayer(p) for p in players_data]
    
    # Pre-compute growth schedules
    growth_caches = {}
    train_carries = {}
    for player in players:
        player_id = str(player.id)
        growth_caches[player_id] = compile_growth_schedule(
            player.growth_shape,
            player.growth_peak_age,
            total_weeks=160
        )
        from match_engine.constants import GOALKEEPER_ATTRS, OUTFIELD_ATTRS
        attrs_list = GOALKEEPER_ATTRS if player.is_goalkeeper else OUTFIELD_ATTRS
        train_carries[player_id] = {a: 0.0 for a in attrs_list}
    
    # Track yearly snapshots
    yearly_snapshots = []
    yearly_dp_breakdown = []
    
    # Initial snapshot (16y1)
    year = 16
    month = 1
    snapshot = {
        "year": year,
        "month": month,
        "players": []
    }
    dp_breakdown = {
        "year": year,
        "month": month,
        "players": []
    }
    
    for player in players:
        snapshot["players"].append({
            "name": player.name,
            "age_months": player.actual_age_months,
            "training_weeks": player.training_age_weeks,
            "attributes": player.attributes.copy(),
            "potential": player.potential,
            "profile_pic": getattr(player, 'profile_pic', None)
        })
        # Calculate DP pools at this age
        total_base = player.potential * player.base_training_pct
        total_growth = player.potential * player.growth_training_pct
        dp_breakdown["players"].append({
            "name": player.name,
            "birth_dp": player.potential * player.birth_dev_pct,
            "base_training_total": total_base,
            "growth_training_total": total_growth,
            "base_training_this_year": 0.0,
            "growth_training_this_year": 0.0
        })
    
    yearly_snapshots.append(snapshot)
    yearly_dp_breakdown.append(dp_breakdown)
    
    # Simulate years (each year = 10 training weeks + offseason)
    for year_num in range(1, request.years_to_simulate + 1):
        # Capture training weeks before training for each player
        player_training_weeks_before = {}
        for player in players:
            player_id = str(player.id)
            player_training_weeks_before[player_id] = player.training_age_weeks
        
        # Train for 10 weeks (1 season)
        season_totals = train_one_season_with_growth(
            players,
            growth_caches,
            train_carries,
            training_facilities_level=request.training_facilities,
            primary_program=request.primary_program,
            primary_share=request.primary_share,
            secondary_program=request.secondary_program,
            secondary_share=request.secondary_share,
            general_share=request.general_share,
            season_weeks=10,
            total_weeks=160,
            DP_PER_ATTR_POINT=10.0
        )
        
        # Calculate current year
        current_year = 16 + year_num
        current_month = 1
        
        snapshot = {
            "year": current_year,
            "month": current_month,
            "players": []
        }
        dp_breakdown = {
            "year": current_year,
            "month": current_month,
            "players": []
        }
        
        for player in players:
            player_id = str(player.id)
            nom_total, asg_total = season_totals.get(player_id, (0.0, 0.0))
            
            snapshot["players"].append({
                "name": player.name,
                "age_months": player.actual_age_months,
                "training_weeks": player.training_age_weeks,
                "attributes": player.attributes.copy(),
                "potential": player.potential,
                "profile_pic": getattr(player, 'profile_pic', None)
            })
            
            # Calculate DP breakdown for this year
            total_base = player.potential * player.base_training_pct
            total_growth = player.potential * player.growth_training_pct
            base_per_week = total_base / 160 if player.training_age_weeks <= 160 else 0.0
            
            # Growth DP this year (sum of the 10 weeks we just trained)
            # Note: train_player_week uses training_age_weeks directly as index (not training_age_weeks - 1)
            # So if training_age_weeks = 1, it uses cache[1] (week 2), then increments to 2
            # If we started at training_week_before = 1 and trained 10 weeks:
            # - Used cache indices: [1, 2, 3, ..., 10] (which are weeks 2-11 in the cache)
            growth_this_year = 0.0
            training_week_before = player_training_weeks_before[player_id]
            if player.training_age_weeks <= 160:
                # train_player_week uses the current training_age_weeks as the index before incrementing
                # So we use indices training_week_before to (training_week_before + 9) inclusive
                start_idx = training_week_before
                end_idx = min(training_week_before + 10, len(growth_caches[player_id]))
                for idx in range(start_idx, end_idx):
                    if 0 <= idx < len(growth_caches[player_id]):
                        growth_this_year += total_growth * growth_caches[player_id][idx]
            
            base_this_year = base_per_week * 10 if player.training_age_weeks <= 160 else 0.0
            
            dp_breakdown["players"].append({
                "name": player.name,
                "birth_dp": player.potential * player.birth_dev_pct,
                "base_training_total": total_base,
                "growth_training_total": total_growth,
                "base_training_this_year": base_this_year,
                "growth_training_this_year": growth_this_year,
                "nominal_used_this_year": nom_total,
                "assigned_dp_this_year": asg_total
            })
        
        yearly_snapshots.append(snapshot)
        yearly_dp_breakdown.append(dp_breakdown)
    
    # Convert to response format
    response_players = []
    for snapshot in yearly_snapshots:
        response_players.append(snapshot)
    
    return DevelopPlayersResponse(
        players=response_players,
        development_points=yearly_dp_breakdown
    )
