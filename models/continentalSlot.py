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


class ContinentalSlot(Base):
    __tablename__ = "continental_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id"),
        nullable=False,
    )

    competition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("continental_competitions.id"),
        nullable=False,
    )

    slot_count = Column(Integer, nullable=False)
