"""add_youth_academy_tables

Revision ID: c7d9e8f2a3b4
Revises: b5c8e9f1a2d3
Create Date: 2026-01-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7d9e8f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'b5c8e9f1a2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add youth_prospects and youth_academy_players tables."""
    
    # Create youth_prospects table
    op.create_table(
        'youth_prospects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_mode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('talent_rating', sa.String(), nullable=False),
        sa.Column('is_goalkeeper', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('nationality', sa.String(), nullable=True),
        sa.Column('skin_tone', sa.String(), nullable=True),
        sa.Column('profile_pic', sa.String(), nullable=True),
        sa.Column('potential_min', sa.Integer(), nullable=False),
        sa.Column('potential_max', sa.Integer(), nullable=False),
        sa.Column('actual_potential', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='available'),
        sa.Column('promoted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ),
        sa.ForeignKeyConstraint(['game_mode_id'], ['game_modes.id'], ),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ),
    )
    
    # Create youth_academy_players table
    op.create_table(
        'youth_academy_players',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('club_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prospect_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('game_mode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('week_joined', sa.Integer(), nullable=False),
        sa.Column('weeks_in_academy', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weeks_to_promotion', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_goalkeeper', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('nationality', sa.String(), nullable=True),
        sa.Column('skin_tone', sa.String(), nullable=True),
        sa.Column('profile_pic', sa.String(), nullable=True),
        sa.Column('talent_rating', sa.String(), nullable=False),
        sa.Column('potential', sa.Integer(), nullable=False),
        sa.Column('birth_dev_pct', sa.Float(), nullable=True),
        sa.Column('base_training_pct', sa.Float(), nullable=True),
        sa.Column('growth_training_pct', sa.Float(), nullable=True),
        sa.Column('growth_shape', sa.Float(), nullable=True),
        sa.Column('growth_peak_age', sa.Float(), nullable=True),
        sa.Column('growth_width', sa.Float(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('attribute_ranges', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('position_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('gainable_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('training_program', sa.String(), nullable=True),
        sa.Column('actual_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('non_playing_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('promoted_to_player_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('promoted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ),
        sa.ForeignKeyConstraint(['prospect_id'], ['youth_prospects.id'], ),
        sa.ForeignKeyConstraint(['game_mode_id'], ['game_modes.id'], ),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ),
        sa.ForeignKeyConstraint(['promoted_to_player_id'], ['players.id'], ),
    )


def downgrade() -> None:
    """Downgrade schema: Drop youth academy tables."""
    op.drop_table('youth_academy_players')
    op.drop_table('youth_prospects')
