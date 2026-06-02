"""mes: Phase 169 — headcount tracking and labor density snapshots

Adds:
  - mes_labor_types.category (LaborCategory enum: ACTIVE/TRANSFER/PERMIT/BREAK/OVERTIME)
  - mes_hourly_labor_snapshots table (O(1) read model for supervisor headcount queries)
  - mes_hourly_production_snapshots: employees_qty, paid_hrs_total, gained_hrs_total

Revision ID: 013_labor_headcount
Revises: 012_labor_collaborator_link
Create Date: 2026-06-02
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '013_labor_headcount'
down_revision: Union[str, None] = '012_labor_collaborator_link'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add category to mes_labor_types
    op.add_column(
        'mes_labor_types',
        sa.Column('category', sa.String(length=20), server_default='ACTIVE', nullable=False),
    )

    # 2. Create mes_hourly_labor_snapshots table
    op.create_table(
        'mes_hourly_labor_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),

        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('production_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=False),  # 0–23

        # Estado subdividido
        sa.Column('headcount_active', sa.Integer(), server_default='0', nullable=False),
        sa.Column('headcount_on_permit', sa.Integer(), server_default='0', nullable=False),
        sa.Column('headcount_transferred_in', sa.Integer(), server_default='0', nullable=False),
        sa.Column('headcount_transferred_out', sa.Integer(), server_default='0', nullable=False),

        # Tiempo efectivo en esa hora
        sa.Column('total_labor_minutes', sa.Numeric(10, 2), server_default='0', nullable=False),
        sa.Column('paid_hrs', sa.Numeric(8, 4), server_default='0', nullable=False),
        # gained_hrs actualizado por eventos de producción (piezas), no por labor events
        sa.Column('gained_hrs', sa.Numeric(8, 4), server_default='0', nullable=False),

        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id']),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
        sa.UniqueConstraint(
            'resource_id', 'date', 'hour', 'company_id',
            name='uq_resource_hourly_labor',
        ),
    )
    op.create_index(
        'ix_hourly_labor_resource_date',
        'mes_hourly_labor_snapshots',
        ['resource_id', 'date'],
    )

    # 3. Extend mes_hourly_production_snapshots with labor fields
    op.add_column(
        'mes_hourly_production_snapshots',
        sa.Column('employees_qty', sa.Integer(), server_default='0', nullable=False),
    )
    op.add_column(
        'mes_hourly_production_snapshots',
        sa.Column('paid_hrs_total', sa.Numeric(8, 4), server_default='0', nullable=False),
    )
    op.add_column(
        'mes_hourly_production_snapshots',
        sa.Column('gained_hrs_total', sa.Numeric(8, 4), server_default='0', nullable=False),
    )


def downgrade() -> None:
    # 3. Remove labor fields from production snapshots
    op.drop_column('mes_hourly_production_snapshots', 'gained_hrs_total')
    op.drop_column('mes_hourly_production_snapshots', 'paid_hrs_total')
    op.drop_column('mes_hourly_production_snapshots', 'employees_qty')

    # 2. Drop hourly labor snapshots table
    op.drop_index('ix_hourly_labor_resource_date', table_name='mes_hourly_labor_snapshots')
    op.drop_table('mes_hourly_labor_snapshots')

    # 1. Remove category from labor types
    op.drop_column('mes_labor_types', 'category')
