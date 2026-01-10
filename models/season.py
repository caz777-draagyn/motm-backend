import uuid
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Season(Base):
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)

    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False)
