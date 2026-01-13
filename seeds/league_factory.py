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
    if tier == 1:
        return dict(
            promote_direct=0,
            promote_playoff=0,
            relegate_direct=2,
            relegate_playoff=2,
        )
    return dict(
        promote_direct=2,
        promote_playoff=2,
        relegate_direct=2,
        relegate_playoff=2,
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
