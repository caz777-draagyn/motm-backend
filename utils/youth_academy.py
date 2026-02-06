"""
Youth Academy module: Prospect generation, academy management, and information reveal system.
"""

import random
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from utils.player_generation import (
    create_player_data,
    sample_potential,
    OUTFIELD_ATTRS,
    GOALKEEPER_ATTRS
)


# Talent rating ranges (potential mapping)
TALENT_RANGES = {
    "Elite": (2700, 3000),
    "Great": (2200, 2699),
    "Good": (1700, 2199),
    "Mediocre": (1200, 1699),
    "Poor": (200, 1199),
}


def assign_talent_rating(potential: int, is_goalkeeper: bool = False) -> Tuple[str, int, int]:
    """
    Assign talent rating based on potential value.
    
    Args:
        potential: Actual potential value
        is_goalkeeper: Whether player is goalkeeper (affects max potential)
    
    Returns:
        Tuple of (rating_string, min_potential, max_potential) for this rating
    """
    # GK potential is scaled down, so adjust ranges if needed
    # For now, use same ranges regardless of position
    for rating, (min_pot, max_pot) in TALENT_RANGES.items():
        if min_pot <= potential <= max_pot:
            return (rating, min_pot, max_pot)
    
    # Fallback (shouldn't happen with normal generation)
    if potential < TALENT_RANGES["Poor"][0]:
        return ("Poor", TALENT_RANGES["Poor"][0], TALENT_RANGES["Poor"][1])
    elif potential > TALENT_RANGES["Elite"][1]:
        return ("Elite", TALENT_RANGES["Elite"][0], TALENT_RANGES["Elite"][1])
    
    return ("Poor", 200, 1199)


def get_prospect_count(youth_facilities_level: int) -> int:
    """
    Calculate number of prospects generated per week based on youth facility level.
    
    Args:
        youth_facilities_level: Youth facilities level (0-10)
    
    Returns:
        Number of prospects (range based on level)
    """
    level = max(0, min(10, youth_facilities_level))
    
    if level == 0:
        return random.randint(1, 2)
    elif level <= 5:
        # Levels 1-5: 2-4 prospects
        return random.randint(2, 4)
    else:
        # Levels 6-10: 5-8 prospects
        return random.randint(5, 8)


def get_profile_picture_folder(heritage_group: Optional[str] = None) -> str:
    """
    Get the folder name for profile pictures based on heritage group.
    
    Args:
        heritage_group: Heritage group name (e.g., "ENG_Mainstream", "ENG_WestAfrica")
                       If None, defaults to "Anglosphere" folder
    
    Returns:
        Folder name string (e.g., "BritishIsles", "AfricaWest", "Anglosphere")
    """
    from .name_data import HERITAGE_PICTURE_FOLDER_MAP
    
    # Determine folder based on heritage group
    if heritage_group and heritage_group in HERITAGE_PICTURE_FOLDER_MAP:
        folder_name = HERITAGE_PICTURE_FOLDER_MAP[heritage_group]
    else:
        folder_name = "Anglosphere"  # Default fallback
    
    # Verify folder exists, fallback to Anglosphere if not
    gfx_path = os.path.join("gfx", folder_name)
    if not os.path.exists(gfx_path):
        return "Anglosphere"
    
    # Check if folder has PNG files, fallback if empty
    png_files = [f for f in os.listdir(gfx_path) if f.lower().endswith('.png')]
    if not png_files and folder_name != "Anglosphere":
        return "Anglosphere"
    
    return folder_name


def get_profile_picture(heritage_group: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Randomly select a profile picture from appropriate folder based on heritage group.
    
    Args:
        heritage_group: Heritage group name (e.g., "ENG_Mainstream", "ENG_WestAfrica")
                       If None, defaults to "Anglosphere" folder
    
    Returns:
        Tuple of (filename, folder_name) or (None, None) if directory doesn't exist
        Example: ("f079ba1f-...png", "BritishIsles")
    """
    folder_name = get_profile_picture_folder(heritage_group)
    gfx_path = os.path.join("gfx", folder_name)
    
    if not os.path.exists(gfx_path):
        return None, None
    
    # Get all PNG files
    png_files = [f for f in os.listdir(gfx_path) if f.lower().endswith('.png')]
    if not png_files:
        return None, None
    
    return random.choice(png_files), folder_name


def generate_weekly_prospects(
    club_id: UUID,
    game_mode_id: UUID,
    season_id: Optional[UUID],
    week_number: int,
    youth_facilities_level: int,
    is_goalkeeper: bool = False,
    nationality: Optional[str] = None,
    heritage_options: Optional[List[str]] = None
) -> List[Dict]:
    """
    Generate prospects for a club this week.
    
    Args:
        club_id: Club UUID
        game_mode_id: Game mode UUID
        season_id: Season UUID (optional)
        week_number: Current week number
        youth_facilities_level: Youth facilities level (0-10)
        is_goalkeeper: Whether to generate goalkeepers only
        nationality: Optional nationality code to use for all prospects
        heritage_options: Optional list of heritage country codes to choose from
    
    Returns:
        List of prospect dictionaries with all data needed for YouthProspect model
    """
    num_prospects = get_prospect_count(youth_facilities_level)
    prospects = []
    
    for _ in range(num_prospects):
        # Generate full player data (hidden from manager initially)
        player_data = create_player_data(
            club_id=str(club_id),
            youth_facilities=youth_facilities_level,
            is_goalkeeper=is_goalkeeper,
            youth_player=False,
            nationality=nationality,
            heritage_options=heritage_options
        )
        
        # Assign talent rating
        actual_potential = player_data["potential"]
        talent_rating, potential_min, potential_max = assign_talent_rating(
            actual_potential, is_goalkeeper
        )
        
        # Use heritage group from player_data if available, otherwise determine it
        heritage_group = player_data.get("heritage_group")
        if not heritage_group:
            from utils.name_generation import select_heritage_group
            player_nationality = player_data.get("nationality", "ENG")
            heritage_group = select_heritage_group(player_nationality)
        
        # Get profile picture based on heritage group (returns filename and folder)
        profile_pic, profile_pic_folder = get_profile_picture(heritage_group=heritage_group)
        
        prospect = {
            "club_id": club_id,
            "game_mode_id": game_mode_id,
            "season_id": season_id,
            "week_number": week_number,
            "name": player_data["name"],
            "talent_rating": talent_rating,
            "is_goalkeeper": is_goalkeeper,
            "nationality": player_data.get("nationality"),
            "skin_tone": player_data.get("skin_tone"),
            "profile_pic": profile_pic,
            "profile_pic_folder": profile_pic_folder,
            "potential_min": potential_min,
            "potential_max": potential_max,
            "actual_potential": actual_potential,
            "status": "available",
            # Store full player data for promotion (not in DB, but passed to creation)
            "_player_data": player_data  # Hidden field, not stored in DB
        }
        
        prospects.append(prospect)
    
    return prospects


def calculate_attribute_ranges(
    actual_attributes: Dict[str, int],
    weeks_in_academy: int,
    reveal_widths: List[float] = [0.4, 0.3, 0.2, 0.1, 0.0],
    initial_ranges: Optional[Dict[str, Dict[str, int]]] = None
) -> Dict[str, Dict[str, int]]:
    """
    Calculate attribute ranges shown to manager based on weeks in academy.
    Ranges can start asymmetric (not centered on actual value) and gradually narrow.
    
    Args:
        actual_attributes: Dict of attribute_name -> actual_value (1-20)
        weeks_in_academy: Current week count (0-indexed, 0 = week 1)
        reveal_widths: List of width percentages per week (default: 40%, 30%, 20%, 10%, 0%)
        initial_ranges: Optional dict of initial ranges (if None, generates new asymmetric ranges)
    
    Returns:
        Dict of attribute_name -> {"min": int, "max": int}
    """
    # Clamp weeks_in_academy to available reveal widths
    week_idx = min(weeks_in_academy, len(reveal_widths) - 1)
    width_pct = reveal_widths[week_idx]
    
    ranges = {}
    
    for attr_name, actual_value in actual_attributes.items():
        if weeks_in_academy == 0:
            # Week 0: Generate initial asymmetric range
            # Max width is 6 skill points (hard limit)
            calculated_width = int((20 - 1) * width_pct)
            max_width = min(6, calculated_width)
            
            # Ensure we have at least some width
            if max_width < 1:
                max_width = 1
            
            # Bias: Make actual value more likely to be in upper half of range
            # This makes players seem to improve rather than get worse
            # Strategy: Prefer ranges where actual is closer to max than min
            
            # Minimum possible start (ensuring actual is in range)
            min_start = max(1, actual_value - max_width)
            # Maximum possible start (ensuring we don't exceed max)
            max_start = min(actual_value, 20 - max_width)
            
            if min_start > max_start:
                # Edge case: can't fit full width, use symmetric range
                min_val = max(1, actual_value - max_width // 2)
                max_val = min(20, actual_value + max_width // 2)
            else:
                # Bias toward ranges where actual is in upper portion
                # Calculate position of actual value in potential range
                # We want actual to be in upper 60% of range on average
                # Use weighted random: prefer ranges where actual is higher
                
                # Calculate weights: higher weight for ranges where actual is closer to max
                weights = []
                positions = []
                for start in range(min_start, max_start + 1):
                    end = min(20, start + max_width)
                    # Ensure range width doesn't exceed max_width
                    actual_width = end - start
                    if actual_width > max_width:
                        end = start + max_width
                    if end > 20:
                        end = 20
                        start = max(1, end - max_width)
                    
                    # Position of actual in this range (0.0 = at min, 1.0 = at max)
                    if end > start:
                        pos = (actual_value - start) / (end - start)
                    else:
                        pos = 0.5
                    positions.append((start, end, pos))
                    # Higher weight for positions > 0.5 (upper half)
                    # Target average position around 0.7 (upper 70%)
                    # Use exponential weighting that favors positions around 0.7
                    if pos > 0.5:
                        # Favor positions around 0.7
                        # Use a curve that peaks around 0.7
                        if pos <= 0.7:
                            weight = (pos / 0.7) ** 0.5  # Strong increase to 0.7
                        else:
                            # Taper off gently from 0.7 to 1.0, but not too much
                            # Keep some weight for positions above 0.7
                            weight = 0.8 - ((pos - 0.7) / 0.3) ** 1.0  # Gentler taper, higher base
                            weight = max(0.3, weight)  # Minimum weight of 0.3
                    else:
                        # Penalize lower positions more
                        weight = (pos ** 1.5)
                    weights.append(weight)
                
                # Normalize weights
                if sum(weights) > 0:
                    weights = [w / sum(weights) for w in weights]
                    # Weighted random choice
                    chosen_idx = random.choices(range(len(positions)), weights=weights)[0]
                    min_val, max_val, _ = positions[chosen_idx]
                    # Final check: ensure width doesn't exceed max_width
                    if max_val - min_val > max_width:
                        max_val = min_val + max_width
                        if max_val > 20:
                            max_val = 20
                            min_val = max(1, max_val - max_width)
                else:
                    # Fallback: random choice
                    range_start = random.randint(min_start, max_start)
                    min_val = range_start
                    max_val = min(20, range_start + max_width)
                    # Ensure width doesn't exceed max_width
                    if max_val - min_val > max_width:
                        max_val = min_val + max_width
                
                # Ensure actual value is within range (should always be, but double-check)
                if actual_value < min_val:
                    min_val = max(1, actual_value)
                elif actual_value > max_val:
                    max_val = min(20, actual_value)
                
                # Final enforcement: ensure width doesn't exceed max_width
                current_width = max_val - min_val
                if current_width > max_width:
                    # Adjust to fit max_width while keeping actual value in range
                    if actual_value - min_val <= max_width:
                        max_val = min(20, min_val + max_width)
                    else:
                        min_val = max(1, max_val - max_width)
            
            # Final check: ensure width is at most 6
            final_width = max_val - min_val
            if final_width > 6:
                # Adjust to exactly 6 while keeping actual value in range
                if actual_value - min_val <= 6:
                    max_val = min(20, min_val + 6)
                else:
                    min_val = max(1, max_val - 6)
                # Re-check width after adjustment
                final_width = max_val - min_val
                if final_width > 6:
                    # Force to exactly 6, centered on actual if needed
                    if actual_value <= 10:
                        min_val = max(1, actual_value - 3)
                        max_val = min(20, min_val + 6)
                    else:
                        max_val = min(20, actual_value + 3)
                        min_val = max(1, max_val - 6)
            
            # Ensure actual value is in range (final safety check)
            if actual_value < min_val:
                min_val = actual_value
            if actual_value > max_val:
                max_val = actual_value
            
            # Absolute final check: width must be <= 6
            final_width = max_val - min_val
            if final_width > 6:
                # Force width to 6, keeping actual value in range
                center = (min_val + max_val) / 2
                if actual_value <= center:
                    min_val = max(1, actual_value)
                    max_val = min(20, min_val + 6)
                else:
                    max_val = min(20, actual_value)
                    min_val = max(1, max_val - 6)
            
            ranges[attr_name] = {"min": int(min_val), "max": int(max_val)}
        else:
            # Week 1+: Narrow the range toward the actual value
            if initial_ranges and attr_name in initial_ranges:
                # Use stored initial range
                initial_min = initial_ranges[attr_name]["min"]
                initial_max = initial_ranges[attr_name]["max"]
            else:
                # Fallback: calculate symmetric range from current width
                span = 20 - 1
                max_width = int(span * reveal_widths[0])  # Use week 0 width
                initial_min = max(1, actual_value - max_width // 2)
                initial_max = min(20, actual_value + max_width // 2)
            
            # Calculate progress (0.0 = week 0, 1.0 = final week)
            total_weeks = len(reveal_widths) - 1
            if total_weeks > 0:
                progress = week_idx / total_weeks  # 0.0 to 1.0
            else:
                progress = 1.0
            
            if progress >= 1.0 or width_pct == 0:
                # Final week: show exact value
                min_val = actual_value
                max_val = actual_value
            else:
                # Interpolate between initial range and actual value
                # Move min toward actual_value, max toward actual_value
                min_val = int(initial_min + (actual_value - initial_min) * progress)
                max_val = int(initial_max - (initial_max - actual_value) * progress)
                
                # Ensure bounds don't cross actual value
                min_val = min(min_val, actual_value)
                max_val = max(max_val, actual_value)
                
                # Ensure bounds are within valid range
                min_val = max(1, min_val)
                max_val = min(20, max_val)
                
                # Final safety check: actual value must be in range
                if actual_value < min_val:
                    min_val = actual_value
                if actual_value > max_val:
                    max_val = actual_value
            
            ranges[attr_name] = {"min": min_val, "max": max_val}
    
    return ranges


def process_academy_week(academy_players: List, week_number: int) -> None:
    """
    Process one week of academy progression for a list of players.
    Updates weeks_in_academy and recalculates attribute ranges.
    
    Args:
        academy_players: List of YouthAcademyPlayer objects
        week_number: Current week number
    """
    for player in academy_players:
        if player.status != "active":
            continue
        
        # Increment weeks in academy
        player.weeks_in_academy += 1
        
        # Recalculate attribute ranges (more accurate each week)
        if player.actual_attributes:
            player.attribute_ranges = calculate_attribute_ranges(
                player.actual_attributes,
                player.weeks_in_academy
            )


def promote_academy_player(academy_player, db_session) -> 'Player':
    """
    Promote academy player to main team.
    Creates Player record with all data from academy player.
    
    Args:
        academy_player: YouthAcademyPlayer object
        db_session: Database session
    
    Returns:
        Created Player object
    """
    from models.player import Player
    
    # Create Player record
    player = Player(
        game_mode_id=academy_player.game_mode_id,
        name=academy_player.name,
        nationality=academy_player.nationality,
        skin_tone=academy_player.skin_tone,
        position=academy_player.position,
        is_goalkeeper=academy_player.is_goalkeeper,
        actual_age_months=16 * 12,  # 16y0m
        training_age_weeks=0,
        potential=academy_player.potential,
        birth_dev_pct=academy_player.birth_dev_pct,
        base_training_pct=academy_player.base_training_pct,
        growth_training_pct=academy_player.growth_training_pct,
        growth_shape=academy_player.growth_shape,
        growth_peak_age=academy_player.growth_peak_age,
        growth_width=academy_player.growth_width,
        attributes=academy_player.actual_attributes,
        non_playing_attributes=academy_player.non_playing_attributes,
        position_traits=academy_player.position_traits or [],
        gainable_traits=academy_player.gainable_traits or []
    )
    
    db_session.add(player)
    db_session.flush()  # Get player.id
    
    # Update academy player status
    academy_player.status = "promoted"
    academy_player.promoted_to_player_id = player.id
    academy_player.promoted_at = datetime.utcnow()
    
    return player
