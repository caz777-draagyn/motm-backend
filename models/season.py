from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Season(Base):
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)

    season_number = Column(Integer, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)

    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    match_days = relationship("MatchDay", back_populates="season", order_by="MatchDay.day_number")
    cup_seasons = relationship("CupSeason", back_populates="season")