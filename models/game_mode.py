from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class GameMode(Base):
    __tablename__ = "game_modes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String, unique=True, nullable=False)   # "classic", "rapid"
    name = Column(String, nullable=False)
    season_length_days = Column(Integer, nullable=False)
    description = Column(String)
    is_pay_to_win = Column(Boolean, default=False)
    
    # Relationships
    calendar_template = relationship("CalendarTemplate", back_populates="game_mode", uselist=False)

