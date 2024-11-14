"""Change datetime columns to string

Revision ID: 11cf37f4b44f
Revises: 17daad9f746b
Create Date: 2024-11-14 16:12:16.850020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11cf37f4b44f'
down_revision: Union[str, None] = '17daad9f746b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('bookingslot', 'start_time')
    op.drop_column('bookingslot', 'end_time')


def downgrade() -> None:
    pass
