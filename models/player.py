from uuid import uuid4
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)

    name = Column(String, nullable=False)
    nationality = Column(String)
    birthdate = Column(Date)

    position = Column(String, nullable=False)
