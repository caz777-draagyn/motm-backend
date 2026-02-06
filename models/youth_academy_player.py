from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class YouthAcademyPlayer(Base):
    """
    Players currently in the youth academy.
    Full data stored but revealed gradually to manager through attribute ranges.
    """
    __tablename__ = "youth_academy_players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Club and game context
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("youth_prospects.id"), nullable=True)  # If promoted from prospect
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    
    # Week tracking
    week_joined = Column(Integer, nullable=False)  # Week number when joined academy
    weeks_in_academy = Column(Integer, nullable=False, default=0)  # Current week count
    weeks_to_promotion = Column(Integer, nullable=False)  # 4 or 5 (random)
    
    # Basic info
    name = Column(String, nullable=False)
    is_goalkeeper = Column(Boolean, nullable=False, default=False)
    nationality = Column(String)
    skin_tone = Column(String)
    profile_pic = Column(String, nullable=True)
    talent_rating = Column(String, nullable=False)  # Copied from prospect
    
    # Development data (hidden from manager initially)
    potential = Column(Integer, nullable=False)  # Actual potential
    birth_dev_pct = Column(Float, nullable=True)
    base_training_pct = Column(Float, nullable=True)
    growth_training_pct = Column(Float, nullable=True)
    growth_shape = Column(Float, nullable=True)
    growth_peak_age = Column(Float, nullable=True)
    growth_width = Column(Float, nullable=True)
    
    # Manager-visible data
    position = Column(String, nullable=True)  # Manager-selected position
    attribute_ranges = Column(JSONB, nullable=True)  # {"Finishing": {"min": 8, "max": 15}, ...}
    initial_attribute_ranges = Column(JSONB, nullable=True)  # Initial week 0 ranges (for narrowing)
    position_traits = Column(JSONB, nullable=True, default=list)  # Manager-assigned
    gainable_traits = Column(JSONB, nullable=True, default=list)
    training_program = Column(String, nullable=True)  # Manager-selected special training
    
    # Hidden actual data
    actual_attributes = Column(JSONB, nullable=True)  # {"Finishing": 12, ...} - actual values
    non_playing_attributes = Column(JSONB, nullable=True)  # Hidden initially
    
    # Status and promotion
    status = Column(String(20), nullable=False, default="active")  # "active", "promoted", "released"
    promoted_to_player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)  # If promoted to main team
    promoted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    club = relationship("Club", back_populates="youth_academy_players")
    prospect = relationship("YouthProspect", foreign_keys=[prospect_id])
    game_mode = relationship("GameMode")
    season = relationship("Season")
    promoted_to_player = relationship("Player", foreign_keys=[promoted_to_player_id])
