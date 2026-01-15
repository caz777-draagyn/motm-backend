from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base
import enum

class DayType(enum.Enum):
    """Types of days in the calendar"""
    MAINTENANCE = "maintenance"  # Season update/maintenance window
    REGULAR_MATCH = "regular_match"  # Regular league match day
    PLAYOFF_SEMI = "playoff_semi"  # Playoff semifinal day
    PLAYOFF_FINAL = "playoff_final"  # Playoff final day
    CUP_MATCH = "cup_match"  # Cup match day (domestic or lower league cup)
    TRANSFER_WINDOW = "transfer_window"  # Transfer window open
    # Add more as needed

class CalendarTemplate(Base):
    """
    Defines the calendar structure for a game mode.
    Each template defines which day of the season (1-70 for classic) 
    has what type of activity.
    """
    __tablename__ = "calendar_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), unique=True, nullable=False)
    
    # Template stored as JSON: {day_number: day_type, ...}
    # Example: {1: "maintenance", 2: "maintenance", 3: "regular_match", ...}
    template_json = Column(JSONB, nullable=False)
    
    # Relationships
    game_mode = relationship("GameMode", back_populates="calendar_template")
