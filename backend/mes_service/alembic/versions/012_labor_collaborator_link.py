"""mes: link labor and production runs to HCM collaborators

Revision ID: 012_labor_collaborator_link
Revises: 011_st_sequence_number
Create Date: 2026-06-02
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '012_labor_collaborator_link'
down_revision: Union[str, None] = '011_st_sequence_number'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. mes_labors modifications
    op.add_column('mes_labors', sa.Column('collaborator_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mes_labors', sa.Column('collaborator_name', sa.String(length=200), nullable=True))
    op.add_column('mes_labors', sa.Column('assigned_plant', sa.String(length=100), nullable=True))
    op.add_column('mes_labors', sa.Column('is_deviation', sa.Boolean(), server_default='false', nullable=False))

    # 2. mes_production_runs modifications
    # Drop old string leader/supervisor fields and add UUID + name fields
    op.drop_column('mes_production_runs', 'leader_id')
    op.drop_column('mes_production_runs', 'supervisor_id')
    op.add_column('mes_production_runs', sa.Column('leader_collaborator_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mes_production_runs', sa.Column('supervisor_collaborator_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mes_production_runs', sa.Column('leader_name', sa.String(length=200), nullable=True))
    op.add_column('mes_production_runs', sa.Column('supervisor_name', sa.String(length=200), nullable=True))
    op.add_column('mes_production_runs', sa.Column('status', sa.String(length=50), server_default='SCHEDULED', nullable=False))

    # 3. mes_labor_allocations modifications
    op.alter_column('mes_labor_allocations', 'operator_count', existing_type=sa.INTEGER(), nullable=True)
    op.add_column('mes_labor_allocations', sa.Column('collaborator_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('mes_labor_allocations', sa.Column('role', sa.String(length=50), nullable=False))
    op.add_column('mes_labor_allocations', sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=False))


def downgrade() -> None:
    # 3. mes_labor_allocations downgrade
    op.drop_column('mes_labor_allocations', 'shift_id')
    op.drop_column('mes_labor_allocations', 'role')
    op.drop_column('mes_labor_allocations', 'collaborator_id')
    op.alter_column('mes_labor_allocations', 'operator_count', existing_type=sa.INTEGER(), nullable=False)

    # 2. mes_production_runs downgrade
    op.drop_column('mes_production_runs', 'status')
    op.drop_column('mes_production_runs', 'supervisor_name')
    op.drop_column('mes_production_runs', 'leader_name')
    op.drop_column('mes_production_runs', 'supervisor_collaborator_id')
    op.drop_column('mes_production_runs', 'leader_collaborator_id')
    op.add_column('mes_production_runs', sa.Column('supervisor_id', sa.String(length=100), nullable=True))
    op.add_column('mes_production_runs', sa.Column('leader_id', sa.String(length=100), nullable=True))

    # 1. mes_labors downgrade
    op.drop_column('mes_labors', 'is_deviation')
    op.drop_column('mes_labors', 'assigned_plant')
    op.drop_column('mes_labors', 'collaborator_name')
    op.drop_column('mes_labors', 'collaborator_id')
