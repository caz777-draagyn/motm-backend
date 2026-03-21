from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class LeagueSeasonTeam(Base):
    __tablename__ = "league_season_teams"

    id = Column(UUID(as_uuid=True), primary_key=True)
    league_season_id = Column(UUID(as_uuid=True), ForeignKey("league_seasons.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)

    final_position = Column(Integer)
    points = Column(Integer)
