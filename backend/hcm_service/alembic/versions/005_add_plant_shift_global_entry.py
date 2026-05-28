"""add plant shift and global entry with tenant threshold config

Revision ID: 005_add_plant_shift_global_entry
Revises: 004_merge_heads
Create Date: 2026-05-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '005_add_plant_shift_global_entry'
down_revision: Union[str, Sequence[str], None] = '004_merge_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to collaborators table
    op.add_column('collaborators', sa.Column('assigned_plant', sa.String(length=100), nullable=True))
    op.add_column('collaborators', sa.Column('shift', sa.String(length=50), nullable=True))
    op.add_column('collaborators', sa.Column('global_entry_id', sa.String(length=30), nullable=True))
    
    # Add column to hr_tenant_configs table
    op.add_column('hr_tenant_configs', sa.Column('cross_border_expiry_threshold_days', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove column from hr_tenant_configs table
    op.drop_column('hr_tenant_configs', 'cross_border_expiry_threshold_days')

    # Remove columns from collaborators table
    op.drop_column('collaborators', 'global_entry_id')
    op.drop_column('collaborators', 'shift')
    op.drop_column('collaborators', 'assigned_plant')
