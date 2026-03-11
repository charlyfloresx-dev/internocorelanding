"""MES Pulse Migration: Added ScrapEntry and Quality metrics.
Revision ID: 5e91a2b3c4d5
Revises: 04dfb9667459
Create Date: 2026-03-05 10:36:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '5e91a2b3c4d5'
down_revision = '04dfb9667459'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'mes_scrap_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('production_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason_code', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('operator_id', sa.String(length=50), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('mes_run_metrics_snapshots', sa.Column('quality', sa.Numeric(precision=5, scale=4), server_default='0.0', nullable=False))
    op.alter_column('mes_hourly_production_snapshots', 'production_plan_id', new_column_name='production_run_id')
    op.drop_constraint('mes_hourly_production_snapshots_production_plan_id_fkey', 'mes_hourly_production_snapshots', type_='foreignkey')
    op.create_foreign_key(
        'mes_hourly_production_snapshots_production_run_id_fkey',
        'mes_hourly_production_snapshots', 'mes_production_runs',
        ['production_run_id'], ['id']
    )

def downgrade() -> None:
    op.drop_constraint('mes_hourly_production_snapshots_production_run_id_fkey', 'mes_hourly_production_snapshots', type_='foreignkey')
    op.create_foreign_key(
        'mes_hourly_production_snapshots_production_plan_id_fkey',
        'mes_hourly_production_snapshots', 'mes_production_plans',
        ['production_run_id'], ['id']
    )
    op.alter_column('mes_hourly_production_snapshots', 'production_run_id', new_column_name='production_plan_id')
    op.drop_column('mes_run_metrics_snapshots', 'quality')
    op.drop_table('mes_scrap_entries')
