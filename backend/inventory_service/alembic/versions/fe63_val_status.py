"""Add validation_status to movements

Revision ID: fe63_val_status
Revises: a5c404f77598
Create Date: 2026-04-20 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe63_val_status'
down_revision: Union[str, None] = 'a5c404f77598'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add validation_status column to inventory_movements table
    op.add_column('inventory_movements', sa.Column('validation_status', sa.String(length=20), server_default='CLEAN', nullable=False))
    op.create_index(op.f('ix_inventory_movements_validation_status'), 'inventory_movements', ['validation_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_movements_validation_status'), table_name='inventory_movements')
    op.drop_column('inventory_movements', 'validation_status')
