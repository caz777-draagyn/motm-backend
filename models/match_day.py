from uuid import uuid4
from sqlalchemy import Column, String, Integer, Date, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
from .calendar_template import DayType

class MatchDay(Base):
    """
    Represents a specific day in a season's calendar.
    Generated from CalendarTemplate when a season is created.
    """
    __tablename__ = "match_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False, index=True)
    
    # Day number within the season (1-70 for classic, 1-21 for rapid, etc.)
    day_number = Column(Integer, nullable=False)
    
    # Actual calendar date
    date = Column(Date, nullable=False, index=True)
    
    # Type of day
    day_type = Column(Enum(DayType), nullable=False)
    
    # Week number (1-10 for classic, etc.)
    week_number = Column(Integer, nullable=False)
    
    # Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday)
    day_of_week = Column(Integer, nullable=False)
    
    # Whether matches have been processed/completed for this day
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    season = relationship("Season", back_populates="match_days")
    cup_matches = relationship("CupMatch", back_populates="match_day")
    
    __table_args__ = (
        # Ensure unique day_number per season
        # Could also add unique constraint on (season_id, date)
    )
