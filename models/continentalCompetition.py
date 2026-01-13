from models.base import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class ContinentalCompetition(Base):
    __tablename__ = "continental_competitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    federation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("federations.id"),
        nullable=False,
        index=True,
    )

    key = Column(String, unique=True, nullable=False)  # "ucl"
    name = Column(String, nullable=False)
    prestige = Column(Integer, nullable=False)
