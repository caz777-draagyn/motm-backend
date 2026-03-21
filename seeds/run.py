from database import SessionLocal
from seeds.game_modes import seed_game_modes
from seeds.federations import seed_federations
from seeds.countries import seed_countries

from seeds.domestic_leagues import seed_domestic_leagues
from seeds.federation_leagues import seed_federation_leagues


def run_seeds():
    db = SessionLocal()

    try:
        # 1. Global static data
        seed_game_modes(db)
        seed_federations(db)
        seed_countries(db)

        # 2. League structures (shared factory underneath)
        seed_domestic_leagues(db)
        seed_federation_leagues(db)

    finally:
        db.close()


if __name__ == "__main__":
    run_seeds()
