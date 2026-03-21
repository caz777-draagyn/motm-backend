"""
Utility functions for generating calendar templates and match days.
"""
from datetime import date, timedelta
from models.calendar_template import CalendarTemplate, DayType
from models.match_day import MatchDay
from models.season import Season


def generate_classic_calendar_template() -> dict:
    """
    Generates the calendar template for Classic game mode (70 days, 10 weeks).
    
    Structure:
    - Days 1-2: Maintenance (Monday-Tuesday Week 1)
    - Match days: Monday, Wednesday, Friday, Sunday
    - First match: Wednesday Week 1 (day 3)
    - Last regular match: Monday Week 10 (day 64)
    - Playoff semis: Wednesday Week 10 (day 66)
    - Playoff final: Friday Week 10 (day 68)
    
    Week calculation:
    - Week 1: Mon(1), Tue(2), Wed(3), Thu(4), Fri(5), Sat(6), Sun(7)
    - Week 10: Mon(64), Tue(65), Wed(66), Thu(67), Fri(68), Sat(69), Sun(70)
    """
    template = {}
    
    # Days 1-2: Maintenance
    template["1"] = DayType.MAINTENANCE.value
    template["2"] = DayType.MAINTENANCE.value
    
    # Regular match days: Monday, Wednesday, Friday, Sunday
    for week in range(1, 11):  # Weeks 1-10
        week_start_day = (week - 1) * 7 + 1
        
        if week == 1:
            # Week 1: Skip Mon(1), Tue(2), then Wed(3), Fri(5), Sun(7)
            template[str(week_start_day + 2)] = DayType.REGULAR_MATCH.value  # Wed
            template[str(week_start_day + 4)] = DayType.REGULAR_MATCH.value  # Fri
            template[str(week_start_day + 6)] = DayType.REGULAR_MATCH.value  # Sun
        elif week == 10:
            # Week 10: Mon(64) is last regular match
            template[str(week_start_day)] = DayType.REGULAR_MATCH.value  # Mon
            # Wed and Fri are playoffs (set below)
        else:
            # Weeks 2-9: All match days (Mon, Wed, Fri, Sun)
            template[str(week_start_day)] = DayType.REGULAR_MATCH.value  # Mon
            template[str(week_start_day + 2)] = DayType.REGULAR_MATCH.value  # Wed
            template[str(week_start_day + 4)] = DayType.REGULAR_MATCH.value  # Fri
            template[str(week_start_day + 6)] = DayType.REGULAR_MATCH.value  # Sun
    
    # Playoff days (Week 10)
    week_10_start = 64  # Monday Week 10
    template[str(week_10_start + 2)] = DayType.PLAYOFF_SEMI.value  # Wed (day 66)
    template[str(week_10_start + 4)] = DayType.PLAYOFF_FINAL.value  # Fri (day 68)
    
    return template


def create_calendar_template_for_game_mode(db, game_mode_id: str) -> CalendarTemplate:
    """Creates a calendar template for a game mode."""
    if game_mode_id is None:
        raise ValueError("game_mode_id is required")
    
    # For now, only classic mode is defined
    # TODO: Add rapid mode and others
    template_data = generate_classic_calendar_template()
    
    template = CalendarTemplate(
        game_mode_id=game_mode_id,
        template_json=template_data
    )
    
    db.add(template)
    return template


def generate_match_days_for_season(db, season: Season) -> list[MatchDay]:
    """
    Generates MatchDay records for a season based on its game mode's calendar template.
    
    Args:
        db: Database session
        season: Season object with start_date set
        
    Returns:
        List of created MatchDay objects
    """
    if not season.start_date:
        raise ValueError("Season must have a start_date to generate match days")
    
    # Get calendar template for this game mode
    template = db.query(CalendarTemplate).filter(
        CalendarTemplate.game_mode_id == season.game_mode_id
    ).first()
    
    if not template:
        raise ValueError(f"No calendar template found for game_mode_id {season.game_mode_id}")
    
    match_days = []
    current_date = season.start_date
    
    for day_number in range(1, season.game_mode.season_length_days + 1):
        day_type_str = template.template_json.get(str(day_number))
        
        if day_type_str:
            # Calculate week number and day of week
            week_number = ((day_number - 1) // 7) + 1
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            
            match_day = MatchDay(
                season_id=season.id,
                day_number=day_number,
                date=current_date,
                day_type=DayType(day_type_str),
                week_number=week_number,
                day_of_week=day_of_week,
                is_completed=False
            )
            
            match_days.append(match_day)
            db.add(match_day)
        
        # Move to next day (always increment, even if not a match day)
        current_date = current_date + timedelta(days=1)
    
    return match_days
