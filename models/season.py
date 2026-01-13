from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Season(Base):
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)

    season_number = Column(Integer, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)

    is_active = Column(Boolean, default=True, nullable=False)