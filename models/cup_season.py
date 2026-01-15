from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class CupSeason(Base):
    """
    Links a cup competition to a specific season.
    Tracks the cup's progress through the season.
    """
    __tablename__ = "cup_seasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cup_competition_id = Column(UUID(as_uuid=True), ForeignKey("cup_competitions.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled, in_progress, completed
    current_round = Column(Integer, nullable=True)  # Current round number (1 = first round, etc.)
    
    # Configuration/structure stored as JSON
    # e.g., {"rounds": 6, "teams_per_round": [64, 32, 16, 8, 4, 2]}
    config_json = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    cup_competition = relationship("CupCompetition", back_populates="cup_seasons")
    season = relationship("Season", back_populates="cup_seasons")
    cup_matches = relationship("CupMatch", back_populates="cup_season")
