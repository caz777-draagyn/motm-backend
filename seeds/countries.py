from sqlalchemy.orm import Session
from models.country import Country
from models.federation import Federation

COUNTRIES = [
    # UEFA
    {"code": "ENG", "name": "England", "fed": "UEFA", "league": True},
    {"code": "ESP", "name": "Spain", "fed": "UEFA", "league": True},
    {"code": "ITA", "name": "Italy", "fed": "UEFA", "league": True},
    {"code": "ISL", "name": "Iceland", "fed": "UEFA", "league": False},

    # CAF
    {"code": "NGA", "name": "Nigeria", "fed": "CAF", "league": True},
    {"code": "GHA", "name": "Ghana", "fed": "CAF", "league": False},
    {"code": "KEN", "name": "Kenya", "fed": "CAF", "league": False},

    # AFC
    {"code": "JPN", "name": "Japan", "fed": "AFC", "league": True},
    {"code": "KOR", "name": "South Korea", "fed": "AFC", "league": True},
    {"code": "PHI", "name": "Philippines", "fed": "AFC", "league": False},
]


def seed_countries(db: Session) -> None:
    federations = {
        f.key: f for f in db.query(Federation).all()
    }

    for c in COUNTRIES:
        existing = (
            db.query(Country)
            .filter(Country.code == c["code"])
            .one_or_none()
        )

        if existing:
            continue

        db.add(
            Country(
                code=c["code"],
                name=c["name"],
                federation_id=federations[c["fed"]].id,
                has_domestic_league=c["league"],
                ranking_points=0,
            )
        )

    db.commit()
