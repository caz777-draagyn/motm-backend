import uuid
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class GameMode(Base):
    __tablename__ = "game_modes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)   # classic, rapid
    name = Column(String, nullable=False)

    season_length_days = Column(Integer, nullable=False)
    allow_microtransactions = Column(Boolean, default=False)
