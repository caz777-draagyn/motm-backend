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


class Federation(Base):
    __tablename__ = "federations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

