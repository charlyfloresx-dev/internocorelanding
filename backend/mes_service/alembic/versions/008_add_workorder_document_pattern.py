"""mes: WorkOrder document+lines pattern — missing tables + tenant_id + wo_type + WorkOrderLine

Revision ID: 008_add_workorder_document_pattern
Revises: 007_add_workorder_alias_release_date
Create Date: 2026-05-28

Changes:
  1. Add tenant_id (nullable) to all existing MES tables that inherit MultiTenantBase
  2. Create missing domain tables: downtime_reasons, downtimes, labor_types, labors,
     manufacturing_ledger, tracking
  3. Add wo_type (WOType enum) + rout_id (UUID) to mes_work_orders
  4. Create mes_work_order_lines (Documento+Líneas pattern)

Note on tenant_id: added as nullable because mes_db is always freshly migrated
(0 rows existed before this migration). Application always sets tenant_id = company_id on insert.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '008_wo_doc_pattern'
down_revision: Union[str, None] = '007_wo_alias'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables from prior migrations that are missing tenant_id
_EXISTING_TABLES = [
    'mes_resources',
    'mes_work_orders',
    'mes_standard_times',
    'mes_production_plans',
    'mes_hourly_production_snapshots',
    'mes_production_runs',
    'mes_downtime_events',
    'mes_labor_allocations',
    'mes_run_metrics_snapshots',
    'mes_shifts',
]


def upgrade() -> None:
    # ── 0. Create PostgreSQL enum types (idempotent — safe on re-run) ───────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE wotype AS ENUM (
                'NON_STANDARD','STANDARD','REPAIR','REWORK','TEST','TOOLING','SCRAP_REPLACEMENT'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE workorderlinetype AS ENUM ('MATERIAL_INPUT','PLANNED_OUTPUT','SCRAP');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE workorderlinestatus AS ENUM ('PENDING','IN_PROGRESS','COMPLETED','CANCELLED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ── 1. Add tenant_id to all existing MES tables ──────────────────────────
    for table in _EXISTING_TABLES:
        op.add_column(table, sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index(f'ix_{table}_tenant_id', table, ['tenant_id'], unique=False)

    # ── 2. Create mes_downtime_reasons ────────────────────────────────────────
    op.create_table(
        'mes_downtime_reasons',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mes_downtime_reasons_code', 'mes_downtime_reasons', ['code'], unique=False)
    op.create_index('ix_mes_downtime_reasons_company_id', 'mes_downtime_reasons', ['company_id'], unique=False)
    op.create_index('ix_mes_downtime_reasons_tenant_id', 'mes_downtime_reasons', ['tenant_id'], unique=False)

    # ── 3. Create mes_downtimes ───────────────────────────────────────────────
    op.create_table(
        'mes_downtimes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('guid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('production_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assign_to_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('action_taken', sa.String(500), nullable=True),
        sa.Column('root_cause', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='OPEN'),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_escalation_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
        sa.ForeignKeyConstraint(['reason_id'], ['mes_downtime_reasons.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guid', name='uq_mes_downtimes_guid'),
    )
    op.create_index('ix_mes_downtimes_company_id', 'mes_downtimes', ['company_id'], unique=False)
    op.create_index('ix_mes_downtimes_tenant_id', 'mes_downtimes', ['tenant_id'], unique=False)
    op.create_index('ix_mes_downtimes_production_run_id', 'mes_downtimes', ['production_run_id'], unique=False)

    # ── 4. Create mes_labor_types ─────────────────────────────────────────────
    op.create_table(
        'mes_labor_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(250), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mes_labor_types_company_id', 'mes_labor_types', ['company_id'], unique=False)
    op.create_index('ix_mes_labor_types_tenant_id', 'mes_labor_types', ['tenant_id'], unique=False)

    # ── 5. Create mes_labors ──────────────────────────────────────────────────
    op.create_table(
        'mes_labors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('production_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_number', sa.Integer(), nullable=True),
        sa.Column('clock_in', sa.DateTime(timezone=True), nullable=False),
        sa.Column('clock_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active_labor', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('type_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
        sa.ForeignKeyConstraint(['type_id'], ['mes_labor_types.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mes_labors_company_id', 'mes_labors', ['company_id'], unique=False)
    op.create_index('ix_mes_labors_tenant_id', 'mes_labors', ['tenant_id'], unique=False)
    op.create_index('ix_mes_labors_production_run_id', 'mes_labors', ['production_run_id'], unique=False)

    # ── 6. Create mes_manufacturing_ledger ────────────────────────────────────
    op.create_table(
        'mes_manufacturing_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('production_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('qty', sa.Numeric(18, 4), nullable=False, server_default='1.0'),
        sa.Column('transaction_type', sa.String(20), nullable=False, server_default='SCAN'),
        sa.Column('external_folio', sa.String(100), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        sa.Column('local_txn_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_synced', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['production_run_id'], ['mes_production_runs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('local_txn_id', name='uq_mes_ledger_local_txn_id'),
    )
    op.create_index('ix_mes_manufacturing_ledger_sku', 'mes_manufacturing_ledger', ['sku'], unique=False)
    op.create_index('ix_mes_manufacturing_ledger_company_id', 'mes_manufacturing_ledger', ['company_id'], unique=False)
    op.create_index('ix_mes_manufacturing_ledger_tenant_id', 'mes_manufacturing_ledger', ['tenant_id'], unique=False)
    op.create_index('ix_mes_manufacturing_ledger_local_txn_id', 'mes_manufacturing_ledger', ['local_txn_id'], unique=True)

    # ── 7. Create mes_tracking ────────────────────────────────────────────────
    op.create_table(
        'mes_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_sku', sa.String(100), nullable=False),
        sa.Column('series', sa.String(100), nullable=True),
        sa.Column('folio', sa.String(100), nullable=True),
        sa.Column('qty', sa.Numeric(18, 4), nullable=False),
        sa.Column('responsible', sa.String(100), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('close_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cost', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mes_tracking_company_id', 'mes_tracking', ['company_id'], unique=False)
    op.create_index('ix_mes_tracking_tenant_id', 'mes_tracking', ['tenant_id'], unique=False)

    # ── 8. Add wo_type + rout_id to mes_work_orders ───────────────────────────
    op.add_column('mes_work_orders',
        sa.Column('wo_type',
            postgresql.ENUM('NON_STANDARD', 'STANDARD', 'REPAIR', 'REWORK', 'TEST', 'TOOLING', 'SCRAP_REPLACEMENT',
                            name='wotype', create_type=False),
            nullable=True))
    op.add_column('mes_work_orders',
        sa.Column('rout_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_mes_work_orders_wo_type', 'mes_work_orders', ['wo_type'], unique=False)

    # ── 9. Create mes_work_order_lines ────────────────────────────────────────
    op.create_table(
        'mes_work_order_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('line_type',
            postgresql.ENUM('MATERIAL_INPUT', 'PLANNED_OUTPUT', 'SCRAP', name='workorderlinetype', create_type=False),
            nullable=False),
        sa.Column('item_code', sa.String(100), nullable=False),
        sa.Column('item_description', sa.String(200), nullable=True),
        sa.Column('planned_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('actual_quantity', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('uom', sa.String(20), nullable=True),
        sa.Column('status',
            postgresql.ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='workorderlinestatus', create_type=False),
            nullable=False, server_default='PENDING'),
        sa.Column('bom_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['mes_work_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_order_id', 'line_number', name='uq_wo_line_number'),
    )
    op.create_index('ix_mes_work_order_lines_work_order_id', 'mes_work_order_lines', ['work_order_id'], unique=False)
    op.create_index('ix_mes_work_order_lines_line_type', 'mes_work_order_lines', ['line_type'], unique=False)
    op.create_index('ix_mes_work_order_lines_item_code', 'mes_work_order_lines', ['item_code'], unique=False)
    op.create_index('ix_mes_work_order_lines_company_id', 'mes_work_order_lines', ['company_id'], unique=False)
    op.create_index('ix_mes_work_order_lines_tenant_id', 'mes_work_order_lines', ['tenant_id'], unique=False)


def downgrade() -> None:
    # Reverse order
    op.drop_table('mes_work_order_lines')
    op.drop_index('ix_mes_work_orders_wo_type', table_name='mes_work_orders')
    op.drop_column('mes_work_orders', 'rout_id')
    op.drop_column('mes_work_orders', 'wo_type')
    op.drop_table('mes_tracking')
    op.drop_table('mes_manufacturing_ledger')
    op.drop_table('mes_labors')
    op.drop_table('mes_labor_types')
    op.drop_table('mes_downtimes')
    op.drop_table('mes_downtime_reasons')

    for table in reversed(_EXISTING_TABLES):
        op.drop_index(f'ix_{table}_tenant_id', table_name=table)
        op.drop_column(table, 'tenant_id')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS workorderlinestatus")
    op.execute("DROP TYPE IF EXISTS workorderlinetype")
    op.execute("DROP TYPE IF EXISTS wotype")
