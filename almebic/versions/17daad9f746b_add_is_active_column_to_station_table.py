"""Add is_active column to Station table

Revision ID: 17daad9f746b
Revises: 
Create Date: 2024-11-14 12:17:45.872559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17daad9f746b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stations', sa.Column('is_active', sa.Boolean(),
                  server_default=sa.text('true'), nullable=False))


def downgrade() -> None:
    pass
