from models.game_mode import GameMode
from models.federation import Federation
from seeds.league_factory import generate_federation_leagues


def seed_federation_leagues(db):
    game_modes = db.query(GameMode).all()
    federations = db.query(Federation).all()

    for game_mode in game_modes:
        for federation in federations:
            generate_federation_leagues(
                db=db,
                game_mode_id=game_mode.id,
                federation=federation,
                name_prefix=federation.name,
            )

    db.commit()
