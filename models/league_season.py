from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from .base import Base


class LeagueSeason(Base):
    __tablename__ = "league_seasons"

    id = Column(UUID(as_uuid=True), primary_key=True)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)

    status = Column(String(20), nullable=False, default="scheduled")
    config_json = Column(JSONB, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
