import uuid
import enum
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class AuctionStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class TransferAuction(Base):
    __tablename__ = "transfer_auctions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    selling_club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)

    starting_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False)

    ends_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.OPEN)

class TransferBid(Base):
    __tablename__ = "transfer_bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    auction_id = Column(UUID(as_uuid=True), ForeignKey("transfer_auctions.id"), nullable=False)
    bidding_club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False)

    amount = Column(Integer, nullable=False)
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
