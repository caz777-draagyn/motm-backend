"""add_initial_attribute_ranges

Revision ID: d8e9f0a1b2c3
Revises: c7d9e8f2a3b4
Create Date: 2026-01-19 11:19:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c7d9e8f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add initial_attribute_ranges column to youth_academy_players table."""
    op.add_column(
        'youth_academy_players',
        sa.Column('initial_attribute_ranges', postgresql.JSONB, nullable=True)
    )


def downgrade() -> None:
    """Remove initial_attribute_ranges column from youth_academy_players table."""
    op.drop_column('youth_academy_players', 'initial_attribute_ranges')
