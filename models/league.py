from .base import Base
import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID


class League(Base):
    __tablename__ = "leagues"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,          # ← Python-side default
        nullable=False,
    )
    game_mode_id = Column(
        UUID(as_uuid=True),
        ForeignKey("game_modes.id"),
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )

    # Exactly ONE of these is set
    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id"),
        nullable=True,
        index=True,
    )

    federation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("federations.id"),
        nullable=True,
        index=True,
    )

    tier = Column(Integer, nullable=False)
    division = Column(Integer, nullable=False)

    name = Column(String, nullable=False)
    
    # League type: False = main team league, True = B-team league
    is_b_team_league = Column(Boolean, default=False, nullable=False)

    club_count = Column(Integer, nullable=False)

    promote_direct = Column(Integer, nullable=False)
    promote_playoff = Column(Integer, nullable=False)
    relegate_direct = Column(Integer, nullable=False)
    relegate_playoff = Column(Integer, nullable=False)

    __table_args__ = (
        # No duplicate leagues in same scope
        UniqueConstraint(
            "game_mode_id",
            "country_id",
            "federation_id",
            "tier",
            "division",
            name="uq_league_scope",
        ),
    )