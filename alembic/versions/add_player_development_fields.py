"""add_player_development_fields

Revision ID: b5c8e9f1a2d3
Revises: a467d2d6fa9d
Create Date: 2026-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b5c8e9f1a2d3'
down_revision: Union[str, Sequence[str], None] = 'a467d2d6fa9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alter players table
    op.add_column('players', sa.Column('skin_tone', sa.String(), nullable=True))
    op.alter_column('players', 'position', nullable=True)
    op.add_column('players', sa.Column('is_goalkeeper', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('players', sa.Column('actual_age_months', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('training_age_weeks', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('players', sa.Column('potential', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('birth_dev_pct', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('base_training_pct', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('growth_training_pct', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('growth_shape', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('growth_peak_age', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('growth_width', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('players', sa.Column('non_playing_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('players', sa.Column('position_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'))
    op.add_column('players', sa.Column('gainable_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'))
    
    # Alter clubs table
    op.add_column('clubs', sa.Column('youth_facilities_level', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('clubs', sa.Column('training_facilities_level', sa.Integer(), nullable=False, server_default='5'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns from clubs table
    op.drop_column('clubs', 'training_facilities_level')
    op.drop_column('clubs', 'youth_facilities_level')
    
    # Remove columns from players table
    op.drop_column('players', 'gainable_traits')
    op.drop_column('players', 'position_traits')
    op.drop_column('players', 'non_playing_attributes')
    op.drop_column('players', 'attributes')
    op.drop_column('players', 'growth_width')
    op.drop_column('players', 'growth_peak_age')
    op.drop_column('players', 'growth_shape')
    op.drop_column('players', 'growth_training_pct')
    op.drop_column('players', 'base_training_pct')
    op.drop_column('players', 'birth_dev_pct')
    op.drop_column('players', 'potential')
    op.drop_column('players', 'training_age_weeks')
    op.drop_column('players', 'actual_age_months')
    op.drop_column('players', 'is_goalkeeper')
    op.alter_column('players', 'position', nullable=False)
    op.drop_column('players', 'skin_tone')
