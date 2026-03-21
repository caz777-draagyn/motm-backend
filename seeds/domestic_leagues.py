from models.game_mode import GameMode
from models.country import Country
from seeds.league_factory import generate_domestic_leagues


def seed_domestic_leagues(db):
    game_modes = db.query(GameMode).all()

    for game_mode in game_modes:
        countries = db.query(Country).all()

        for country in countries:
            generate_domestic_leagues(
                db=db,
                game_mode_id=game_mode.id,
                country=country,
                name_prefix=country.name,
            )

    db.commit()