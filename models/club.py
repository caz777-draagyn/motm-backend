import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Club(Base):
    __tablename__ = "clubs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    manager_id = Column(UUID(as_uuid=True), ForeignKey("managers.id"), nullable=False)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)

    name = Column(String, nullable=False)
    balance = Column(Integer, nullable=False, default=0)

    # hierarchy (B-teams etc.)
    parent_club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True)

    parent_club = relationship(
        "Club",
        remote_side=[id],
        backref="child_clubs"
    )
