from sqlalchemy.orm import Session
from models.game_mode import GameMode

GAME_MODES = [
    {
        "key": "classic",
        "name": "Classic",
        "season_length_days": 70,
        "description": "Slow-paced, fair-play mode with no pay-to-win mechanics",
        "is_pay_to_win": False,
    },
    {
        "key": "rapid",
        "name": "Rapid",
        "season_length_days": 21,
        "description": "Accelerated mode with compressed calendar and optional monetization",
        "is_pay_to_win": True,
    },
]

def seed_game_modes(db: Session) -> None:
    for data in GAME_MODES:
        exists = (
            db.query(GameMode)
            .filter(GameMode.key == data["key"])
            .one_or_none()
        )

        if exists:
            continue

        db.add(GameMode(**data))

    db.commit()
