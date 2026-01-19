from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

class Club(Base):
    __tablename__ = "clubs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # User account (manager in game context)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("managers.id"), nullable=False)
    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)
    
    # Country association (for dynamic league system)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True)

    name = Column(String, nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    
    # Training facilities (0-10 scale)
    youth_facilities_level = Column(Integer, nullable=False, default=5)
    training_facilities_level = Column(Integer, nullable=False, default=5)
    
    # B-team hierarchy
    # Main teams: is_b_team=False, parent_club_id=None
    # B-teams: is_b_team=True, parent_club_id points to main team
    is_b_team = Column(Boolean, default=False, nullable=False)
    parent_club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True)

    # Relationships
    manager = relationship("Manager", back_populates="clubs")
    country = relationship("Country", back_populates="clubs")
    youth_prospects = relationship("YouthProspect", back_populates="club")
    youth_academy_players = relationship("YouthAcademyPlayer", back_populates="club")
    
    # Parent/child club relationships (for B-teams)
    parent_club = relationship(
        "Club",
        remote_side=[id],
        foreign_keys=[parent_club_id],
        backref="child_clubs"
    )
    # Explicit child clubs relationship (B-teams belonging to this main team)
    b_teams = relationship(
        "Club",
        foreign_keys=[parent_club_id],
        remote_side=[id],
        backref="main_club"
    )
    
    def get_youth_academy_capacity(self) -> int:
        """
        Calculate youth academy capacity based on youth facilities level.
        Formula: 3 + (youth_facilities_level * 1.2)
        Level 0 → 3 slots, Level 10 → 15 slots
        """
        return int(3 + (self.youth_facilities_level * 1.2))