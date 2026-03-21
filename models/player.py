from uuid import uuid4
from sqlalchemy import Column, String, Date, ForeignKey, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    game_mode_id = Column(UUID(as_uuid=True), ForeignKey("game_modes.id"), nullable=False)

    name = Column(String, nullable=False)
    nationality = Column(String)
    birthdate = Column(Date)
    skin_tone = Column(String)

    position = Column(String, nullable=True)  # Made nullable initially
    
    # Goalkeeper flag
    is_goalkeeper = Column(Boolean, nullable=False, default=False)
    
    # Age tracking
    actual_age_months = Column(Integer, nullable=True)  # Total calendar months
    training_age_weeks = Column(Integer, nullable=False, default=0)  # Training weeks since 16y0m
    
    # Development model
    potential = Column(Integer, nullable=True)  # Development points (200-3000 for outfield, scaled for GK)
    birth_dev_pct = Column(Float, nullable=True)  # Percentage of potential spent at birth
    base_training_pct = Column(Float, nullable=True)  # Percentage for base training
    growth_training_pct = Column(Float, nullable=True)  # Percentage for growth training
    growth_shape = Column(Float, nullable=True)  # Weibull shape parameter
    growth_peak_age = Column(Float, nullable=True)  # Peak growth age in years
    growth_width = Column(Float, nullable=True)  # Growth distribution width
    
    # Attributes stored as JSONB for flexibility
    attributes = Column(JSONB, nullable=True)  # Dict of attribute_name -> value (1-20)
    non_playing_attributes = Column(JSONB, nullable=True)  # Dict: Injury Proneness, Professionalism, Adaptability, Aggression
    position_traits = Column(JSONB, nullable=True, default=list)  # List of position trait strings
    gainable_traits = Column(JSONB, nullable=True, default=list)  # List of gainable trait strings
    
    # ---- Age helper methods ----
    def get_actual_age_ym(self) -> tuple[int, int]:
        """Get actual age as (years, months) tuple."""
        if self.actual_age_months is None:
            return (0, 0)
        y, m = divmod(self.actual_age_months, 12)
        return (y, m)
    
    def get_training_age_ym(self) -> tuple[int, int]:
        """Get training age as (years, months) tuple. 1 training week == 1 'training month' in-season."""
        training_weeks = self.training_age_weeks or 0
        y, m = divmod(training_weeks, 12)
        return (y, m)
    
    def set_actual_age_ym(self, years: int, months: int) -> None:
        """Set actual age from years and months."""
        self.actual_age_months = years * 12 + months
