from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class YouthProspect(Base):
    """
    Prospects available for manager review each week.
    Limited information shown (name, talent rating, profile pic).
    """
    __tablename__ = "youth_prospects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Club and game context
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True)
    
    # Week tracking
    week_number = Column(Integer, nullable=False)  # Which week this prospect appeared
    
    # Basic info (shown to manager)
    name = Column(String, nullable=False)
    talent_rating = Column(String, nullable=False)  # "Elite", "Great", "Good", "Mediocre", "Poor"
    is_goalkeeper = Column(Boolean, nullable=False, default=False)
    nationality = Column(String)
    skin_tone = Column(String)
    profile_pic = Column(String, nullable=True)  # Filename from gfx/Anglosphere
    
    # Potential ranges (for talent rating)
    potential_min = Column(Integer, nullable=False)  # Min potential for this talent rating
    potential_max = Column(Integer, nullable=False)  # Max potential for this talent rating
    actual_potential = Column(Integer, nullable=False)  # Hidden actual value
    
    # Status
    status = Column(String(20), nullable=False, default="available")  # "available", "promoted", "rejected"
    promoted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="youth_prospects")
    game_mode = relationship("GameMode")
    season = relationship("Season")
