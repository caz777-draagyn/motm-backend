from sqlalchemy.orm import Session
from models.federation import Federation

FEDERATIONS = [
    {"key": "UEFA", "name": "Europe"},
    {"key": "CAF", "name": "Africa"},
    {"key": "AFC", "name": "Asia"},
    {"key": "CONMEBOL", "name": "South America"},
    {"key": "CONCACAF", "name": "North & Central America"},
    {"key": "OFC", "name": "Oceania"},
]


def seed_federations(db: Session) -> None:
    for fed in FEDERATIONS:
        existing = (
            db.query(Federation)
            .filter(Federation.key == fed["key"])
            .one_or_none()
        )

        if not existing:
            db.add(Federation(**fed))

    db.commit()
