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


class Country(Base):
    __tablename__ = "countries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    federation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("federations.id"),
        nullable=False,
        index=True,
    )

    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    ranking_points = Column(Integer, nullable=False, default=0)

    has_domestic_league = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    clubs = relationship("Club", back_populates="country")