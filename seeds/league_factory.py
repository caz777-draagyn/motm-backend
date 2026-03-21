from models.league import League
from models.country import Country



MAX_TIER = 4


def divisions_for_tier(tier: int) -> int:
    if tier == 1:
        return 1
    if tier == 2:
        return 2
    if tier == 3:
        return 4
    return 4 * (3 ** (tier - 3))


def tier_rules(tier: int) -> dict:
    """
    Defines promotion/relegation rules for each tier.
    
    Tier 1 (18 teams, 1 division):
    - Positions 15-18: Direct relegation (4 teams)
    - Positions 13-14: Relegation playoff (2 teams)
    - No promotion (top tier)
    
    Tier 2 (18 teams per division, 2 divisions):
    - Top 2 per division: Direct promotion (2 teams per division)
    - Positions 2-3 per division: Promotion playoff (2 teams per division)
    - Bottom 2 per division: Direct relegation (2 teams per division)
    - Positions 15-16 per division: Relegation playoff (2 teams per division)
    
    Tier 3 (18 teams per division, 4 divisions):
    - Top 2 per division: Direct promotion (2 teams per division)
    - Positions 2-3 per division: Promotion playoff (2 teams per division)
    - Bottom 2 per division: Direct relegation (2 teams per division)
    - Positions 15-16 per division: Relegation playoff (2 teams per division)
    
    Tier 4+ (18 teams per division, 3x previous tier):
    - Top 1 per division: Direct promotion (1 team per division)
    - Positions 2-3 per division: Promotion playoff (2 teams per division)
    - Bottom 3 per division: Direct relegation (3 teams per division)
    - Positions 15-17 per division: Relegation playoff (3 teams per division)
    """
    if tier == 1:
        return dict(
            promote_direct=0,      # No promotion from top tier
            promote_playoff=0,     # No promotion from top tier
            relegate_direct=4,     # Positions 15-18 directly relegated
            relegate_playoff=2,    # Positions 13-14 in relegation playoff
        )
    elif tier == 2:
        return dict(
            promote_direct=2,         # Top 2 per division directly promoted
            promote_playoff=2,         # Positions 2-3 per division in promotion playoff
            relegate_direct=2,         # Bottom 2 per division directly relegated
            relegate_playoff=2,        # Positions 15-16 per division in relegation playoff
        )
    elif tier == 3:
        return dict(
            promote_direct=2,         # Top 2 per division directly promoted
            promote_playoff=2,         # Positions 2-3 per division in promotion playoff
            relegate_direct=3,         # Bottom 3 per division directly relegated (positions 16-18)
            relegate_playoff=3,        # Positions 13-15 per division in relegation playoff
        )
    else:  # Tier 4+
        return dict(
            promote_direct=1,         # Top 1 per division directly promoted
            promote_playoff=2,         # Positions 2-3 per division in promotion playoff
            relegate_direct=3,         # Bottom 3 per division directly relegated
            relegate_playoff=3,        # Positions 15-17 per division in relegation playoff
        )


def generate_domestic_leagues(
    *,
    db,
    game_mode_id,
    country,
    name_prefix,
):
    """
    Creates a full league pyramid for either:
    - a country (country_id != None)
    - a federation umbrella (country_id == None)
    """

    for tier in range(1, MAX_TIER + 1):
        rules = tier_rules(tier)

        for division in range(1, divisions_for_tier(tier) + 1):
            exists = (
                db.query(League)
                .filter(
                    League.country_id == country.id,
                    League.tier == tier,
                    League.division == division,
                    League.game_mode_id == game_mode_id,
                )
                .one_or_none()
            )

            if exists:
                continue

            name = f"{name_prefix} Tier {tier} Division {division}"

            db.add(
                League(
                    game_mode_id=game_mode_id,
                    country_id=country.id,
                    tier=tier,
                    division=division,
                    name=name,
                    club_count=18,
                    **rules,
                )
            )


def generate_federation_leagues(
    *,
    db,
    game_mode_id,
    federation,
    name_prefix,
):
    for tier in range(1, MAX_TIER + 1):
        rules = tier_rules(tier)

        for division in range(1, divisions_for_tier(tier) + 1):
            exists = (
                db.query(League)
                .filter(
                    League.game_mode_id == game_mode_id,
                    League.federation_id == federation.id,
                    League.tier == tier,
                    League.division == division,
                )
                .one_or_none()
            )

            if exists:
                continue

            name = f"{name_prefix} Tier {tier} Division {division}"

            db.add(
                League(
                    game_mode_id=game_mode_id,
                    federation_id=federation.id,
                    country_id=None,
                    tier=tier,
                    division=division,
                    name=name,
                    club_count=18,
                    **rules,
                )
            )
