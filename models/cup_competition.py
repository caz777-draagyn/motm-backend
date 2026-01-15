from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base
import enum

class CupType(enum.Enum):
    """Types of cup competitions"""
    DOMESTIC = "domestic"  # Main domestic cup (all teams in country)
    LOWER_LEAGUE = "lower_league"  # Lower league cup (tiers 2-3, or tier 4+, etc.)

class CupCompetition(Base):
    """
    Represents a cup competition structure.
    
    - Domestic Cup: All teams in a country participate
    - Lower League Cup: Specific tiers participate (e.g., Tiers 2-3 together, or Tier 4+ separately)
    """
    __tablename__ = "cup_competitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False, index=True)
    
    # Exactly ONE of these is set (similar to League)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True)
    federation_id = Column(UUID(as_uuid=True), ForeignKey("federations.id"), nullable=True, index=True)
    
    cup_type = Column(Enum(CupType), nullable=False)
    name = Column(String, nullable=False)  # e.g., "FA Cup", "Lower League Cup Tiers 2-3"
    
    # For lower league cups: which tiers participate
    # Stored as JSON array: [2, 3] for tiers 2-3, or [4] for tier 4 only, etc.
    # For domestic cup: null (all tiers participate)
    participating_tiers_json = Column(JSONB, nullable=True)  # JSON array like [2, 3] or [4]
    
    # Whether Tier 1 teams participate (only false for lower league cups)
    tier_1_participates = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    cup_seasons = relationship("CupSeason", back_populates="cup_competition")
