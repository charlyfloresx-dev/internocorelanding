"""add external_token column to tickets

Revision ID: 3aea30dd49d9
Revises: 2f4c8fb2d1de
Create Date: 2026-05-08 10:33:31.772588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3aea30dd49d9'
down_revision: Union[str, None] = '2f4c8fb2d1de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tickets', sa.Column('external_token', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_tickets_external_token'), 'tickets', ['external_token'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tickets_external_token'), table_name='tickets')
    op.drop_column('tickets', 'external_token')
