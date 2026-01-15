from uuid import uuid4
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Manager(Base):
    """
    Represents a user account (manager in the game context).
    A manager can have multiple clubs across different game modes,
    and potentially multiple clubs within the same game mode.
    """
    __tablename__ = "managers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    clubs = relationship("Club", back_populates="manager")