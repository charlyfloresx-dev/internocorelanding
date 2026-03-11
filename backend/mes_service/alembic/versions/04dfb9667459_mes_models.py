"""mes_models

Revision ID: 04dfb9667459
Revises: d6c155a58ce6
Create Date: 2026-03-05 10:10:37.013568

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04dfb9667459'
down_revision = 'd6c155a58ce6'
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.create_table('mes_resources',
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('break_group_id', sa.Uuid(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
    )
    op.create_index(op.f('ix_mes_resources_company_id'), 'mes_resources', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_resources_code'), 'mes_resources', ['code'], unique=False)
    op.create_index(op.f('ix_mes_resources_group_id'), 'mes_resources', ['group_id'], unique=False)
    op.create_table('mes_work_orders',
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('item_code', sa.String(length=100), nullable=False),
        sa.Column('order_quantity', sa.Integer(), nullable=False),
        sa.Column('manufactured_quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('material_status', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
    )
    op.create_index(op.f('ix_mes_work_orders_item_code'), 'mes_work_orders', ['item_code'], unique=False)
    op.create_index(op.f('ix_mes_work_orders_company_id'), 'mes_work_orders', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_work_orders_group_id'), 'mes_work_orders', ['group_id'], unique=False)
    op.create_index(op.f('ix_mes_work_orders_order_number'), 'mes_work_orders', ['order_number'], unique=True)
    op.create_table('mes_standard_times',
        sa.Column('item_code', sa.String(length=100), nullable=False),
        sa.Column('operation_name', sa.String(length=100), nullable=False),
        sa.Column('set_time_hours', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
    )
    op.create_index(op.f('ix_mes_standard_times_group_id'), 'mes_standard_times', ['group_id'], unique=False)
    op.create_index(op.f('ix_mes_standard_times_company_id'), 'mes_standard_times', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_standard_times_item_code'), 'mes_standard_times', ['item_code'], unique=False)
    op.create_table('mes_production_plans',
        sa.Column('work_order_id', sa.UUID(), nullable=False),
        sa.Column('resource_id', sa.UUID(), nullable=False),
        sa.Column('shift_id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('planned_quantity', sa.Integer(), nullable=False),
        sa.Column('actual_quantity', sa.Integer(), nullable=False),
        sa.Column('planned_time_hours', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id']),
        sa.ForeignKeyConstraint(['work_order_id'], ['mes_work_orders.id']),
        sa.UniqueConstraint('resource_id', 'date', 'shift_id', 'company_id', name='uq_production_plan_schedule'),
    )
    op.create_index(op.f('ix_mes_production_plans_company_id'), 'mes_production_plans', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_production_plans_group_id'), 'mes_production_plans', ['group_id'], unique=False)
    op.create_table('mes_hourly_production_snapshots',
        sa.Column('resource_id', sa.UUID(), nullable=False),
        sa.Column('production_plan_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=False),
        sa.Column('goal_quantity', sa.Integer(), nullable=False),
        sa.Column('actual_quantity', sa.Integer(), nullable=False),
        sa.Column('efficiency_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('item_code', sa.String(length=100), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id']),
        sa.ForeignKeyConstraint(['production_plan_id'], ['mes_production_plans.id']),
        sa.UniqueConstraint('resource_id', 'date', 'hour', 'company_id', name='uq_hourly_snapshot'),
    )
    op.create_index(op.f('ix_mes_hourly_production_snapshots_date'), 'mes_hourly_production_snapshots', ['date'], unique=False)
    op.create_index(op.f('ix_mes_hourly_production_snapshots_company_id'), 'mes_hourly_production_snapshots', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_hourly_production_snapshots_group_id'), 'mes_hourly_production_snapshots', ['group_id'], unique=False)
    op.create_index(op.f('ix_mes_hourly_production_snapshots_item_code'), 'mes_hourly_production_snapshots', ['item_code'], unique=False)
    op.create_table('mes_production_runs',
        sa.Column('work_order_id', sa.UUID(), nullable=False),
        sa.Column('resource_id', sa.UUID(), nullable=False),
        sa.Column('shift_id', sa.Uuid(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('leader_id', sa.String(length=100), nullable=True),
        sa.Column('supervisor_id', sa.String(length=100), nullable=True),
        sa.Column('planned_quantity', sa.Integer(), nullable=False),
        sa.Column('actual_quantity', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id']),
        sa.ForeignKeyConstraint(['work_order_id'], ['mes_work_orders.id']),
        sa.UniqueConstraint('resource_id', 'date', 'shift_id', 'company_id', name='uq_production_run_schedule'),
    )
    op.create_index(op.f('ix_mes_production_runs_group_id'), 'mes_production_runs', ['group_id'], unique=False)
    op.create_index(op.f('ix_mes_production_runs_company_id'), 'mes_production_runs', ['company_id'], unique=False)
    op.create_table('mes_downtime_events',
        sa.Column('production_run_id', sa.UUID(), nullable=False),
        sa.Column('reason_code', sa.String(length=100), nullable=False),
        sa.Column('duration_minutes', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('is_planned', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
    )
    op.create_index(op.f('ix_mes_downtime_events_company_id'), 'mes_downtime_events', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_downtime_events_group_id'), 'mes_downtime_events', ['group_id'], unique=False)
    op.create_table('mes_labor_allocations',
        sa.Column('production_run_id', sa.UUID(), nullable=False),
        sa.Column('operator_count', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
    )
    op.create_index(op.f('ix_mes_labor_allocations_company_id'), 'mes_labor_allocations', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_labor_allocations_group_id'), 'mes_labor_allocations', ['group_id'], unique=False)
    op.create_table('mes_run_metrics_snapshots',
        sa.Column('production_run_id', sa.UUID(), nullable=False),
        sa.Column('availability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('efficiency', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('oee', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('tak_time_seconds', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('lmpu_minutes', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
    )
    op.create_index(op.f('ix_mes_run_metrics_snapshots_company_id'), 'mes_run_metrics_snapshots', ['company_id'], unique=False)
    op.create_index(op.f('ix_mes_run_metrics_snapshots_group_id'), 'mes_run_metrics_snapshots', ['group_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mes_run_metrics_snapshots_company_id'), table_name='mes_run_metrics_snapshots')
    op.drop_index(op.f('ix_mes_run_metrics_snapshots_group_id'), table_name='mes_run_metrics_snapshots')
    op.drop_table('mes_run_metrics_snapshots')
    op.drop_index(op.f('ix_mes_labor_allocations_company_id'), table_name='mes_labor_allocations')
    op.drop_index(op.f('ix_mes_labor_allocations_group_id'), table_name='mes_labor_allocations')
    op.drop_table('mes_labor_allocations')
    op.drop_index(op.f('ix_mes_downtime_events_company_id'), table_name='mes_downtime_events')
    op.drop_index(op.f('ix_mes_downtime_events_group_id'), table_name='mes_downtime_events')
    op.drop_table('mes_downtime_events')
    op.drop_index(op.f('ix_mes_production_runs_group_id'), table_name='mes_production_runs')
    op.drop_index(op.f('ix_mes_production_runs_company_id'), table_name='mes_production_runs')
    op.drop_table('mes_production_runs')
    op.drop_index(op.f('ix_mes_hourly_production_snapshots_date'), table_name='mes_hourly_production_snapshots')
    op.drop_index(op.f('ix_mes_hourly_production_snapshots_company_id'), table_name='mes_hourly_production_snapshots')
    op.drop_index(op.f('ix_mes_hourly_production_snapshots_group_id'), table_name='mes_hourly_production_snapshots')
    op.drop_index(op.f('ix_mes_hourly_production_snapshots_item_code'), table_name='mes_hourly_production_snapshots')
    op.drop_table('mes_hourly_production_snapshots')
    op.drop_index(op.f('ix_mes_production_plans_company_id'), table_name='mes_production_plans')
    op.drop_index(op.f('ix_mes_production_plans_group_id'), table_name='mes_production_plans')
    op.drop_table('mes_production_plans')
    op.drop_index(op.f('ix_mes_standard_times_group_id'), table_name='mes_standard_times')
    op.drop_index(op.f('ix_mes_standard_times_company_id'), table_name='mes_standard_times')
    op.drop_index(op.f('ix_mes_standard_times_item_code'), table_name='mes_standard_times')
    op.drop_table('mes_standard_times')
    op.drop_index(op.f('ix_mes_work_orders_item_code'), table_name='mes_work_orders')
    op.drop_index(op.f('ix_mes_work_orders_company_id'), table_name='mes_work_orders')
    op.drop_index(op.f('ix_mes_work_orders_group_id'), table_name='mes_work_orders')
    op.drop_index(op.f('ix_mes_work_orders_order_number'), table_name='mes_work_orders')
    op.drop_table('mes_work_orders')
    op.drop_index(op.f('ix_mes_resources_company_id'), table_name='mes_resources')
    op.drop_index(op.f('ix_mes_resources_code'), table_name='mes_resources')
    op.drop_index(op.f('ix_mes_resources_group_id'), table_name='mes_resources')
    op.drop_table('mes_resources')
