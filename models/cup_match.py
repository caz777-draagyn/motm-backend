from uuid import uuid4
from sqlalchemy import Column, Integer, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class CupMatch(Base):
    """
    Represents a single cup match.
    Single-leg matches (no home/away legs).
    """
    __tablename__ = "cup_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cup_season_id = Column(UUID(as_uuid=True), ForeignKey("cup_seasons.id"), nullable=False, index=True)
    match_day_id = Column(UUID(as_uuid=True), ForeignKey("match_days.id"), nullable=True, index=True)
    
    # Round number (1 = first round, higher = later rounds)
    round_number = Column(Integer, nullable=False)
    
    # Teams (clubs) participating
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)
    
    # Match date (can be different from match_day.date if rescheduled)
    match_date = Column(Date, nullable=False)
    
    # Match result
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Winner (null if not played yet, or if draw - though cups usually have extra time/penalties)
    winner_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True)
    
    # Whether match has been played
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    cup_season = relationship("CupSeason", back_populates="cup_matches")
    match_day = relationship("MatchDay", back_populates="cup_matches")
    home_team = relationship("Club", foreign_keys=[home_team_id], backref="cup_matches_home")
    away_team = relationship("Club", foreign_keys=[away_team_id], backref="cup_matches_away")
    winner = relationship("Club", foreign_keys=[winner_id])
