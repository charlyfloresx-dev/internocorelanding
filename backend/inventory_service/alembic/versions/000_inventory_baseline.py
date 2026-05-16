"""inventory_baseline

Revision ID: 000_inventory_baseline
Revises: None
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_inventory_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _table_exists(name):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return name in sa_inspect(bind).get_table_names()

def _type_exists(name):
    bind = op.get_bind()
    res = bind.execute(sa.text(f"SELECT 1 FROM pg_type WHERE typname = '{name}'"))
    return res.first() is not None

def upgrade() -> None:
    # 0. Create ENUMs
    if not _type_exists('warehousetype'):
        postgresql.ENUM('PHYSICAL', 'VIRTUAL', 'TRANSIT', 'RESOURCE', 'EXT_PARTNER', name='warehousetype').create(op.get_bind())
    if not _type_exists('movementtype'):
        postgresql.ENUM('ENTRY', 'OUTPUT', 'TRANSFER', 'ADJUSTMENT', name='movementtype').create(op.get_bind())
    if not _type_exists('productstatus'):
        postgresql.ENUM('DRAFT', 'ACTIVE', 'INACTIVE', 'DISCONTINUED', name='productstatus').create(op.get_bind())
    if not _type_exists('documentstatus'):
        postgresql.ENUM('DRAFT', 'PROCESSED', 'CANCELLED', name='documentstatus').create(op.get_bind())
    if not _type_exists('customsoperationtype'):
        postgresql.ENUM('IMPORT', 'EXPORT', name='customsoperationtype').create(op.get_bind())
    if not _type_exists('backflusherrortype'):
        postgresql.ENUM('MISSING_BOM', 'INSUFFICIENT_STOCK', 'INVALID_PRODUCT', name='backflusherrortype').create(op.get_bind())
    if not _type_exists('backflushstatus'):
        postgresql.ENUM('PENDING', 'RESOLVED', 'IGNORED', 'FAILED_MANUAL_REVIEW', name='backflushstatus').create(op.get_bind())

    # Helper for Audit + MultiTenant columns
    audit_columns = [
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
    ]

    # 1. inventory_warehouses
    if not _table_exists('inventory_warehouses'):
        op.create_table('inventory_warehouses',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('location', sa.String(length=200), nullable=True),
            sa.Column('is_transit', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('type', postgresql.ENUM(name='warehousetype', create_type=False), server_default='PHYSICAL', nullable=False),
            sa.Column('country_code', sa.String(2), server_default='MX', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_inventory_warehouses_code', 'inventory_warehouses', ['code'])
        op.create_index('ix_inventory_warehouses_company_id', 'inventory_warehouses', ['company_id'])

    # 2. inventory_locations
    if not _table_exists('inventory_locations'):
        op.create_table('inventory_locations',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('warehouse_id', sa.UUID(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('aisle', sa.String(length=10), nullable=True),
            sa.Column('section', sa.String(length=10), nullable=True),
            sa.Column('level', sa.String(length=10), nullable=True),
            sa.Column('bin_slot', sa.String(length=10), nullable=True),
            sa.Column('zone_type', sa.String(20), server_default='STORAGE', nullable=False),
            sa.Column('storage_type', sa.String(20), server_default='DRY', nullable=False),
            sa.Column('is_multisku', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('velocity_code', sa.String(length=1), nullable=True),
            sa.Column('max_capacity_units', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('max_weight_kg', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('width_cm', sa.Numeric(10, 2), server_default='0', nullable=False),
            sa.Column('height_cm', sa.Numeric(10, 2), server_default='0', nullable=False),
            sa.Column('depth_cm', sa.Numeric(10, 2), server_default='0', nullable=False),
            sa.Column('current_units', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('current_weight_kg', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('is_virtual', sa.Boolean(), server_default='false', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('company_id', 'warehouse_id', 'code', name='uq_location_per_warehouse')
        )

    # 3. inventory_movements
    if not _table_exists('inventory_movements'):
        op.create_table('inventory_movements',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('warehouse_id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
            sa.Column('uom_id', sa.UUID(), nullable=False),
            sa.Column('weight', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('unit_price', sa.Numeric(18, 4), server_default='0', nullable=True),
            sa.Column('currency', sa.String(3), server_default='MXN', nullable=False),
            sa.Column('movement_type', sa.String(20), nullable=False),
            sa.Column('available_quantity', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('customs_pedimento_id', sa.UUID(), nullable=True),
            sa.Column('source_movement_id', sa.UUID(), nullable=True),
            sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('concept_id', sa.UUID(), nullable=True),
            sa.Column('location', sa.String(length=50), nullable=True),
            sa.Column('document_type', sa.String(20), nullable=False),
            sa.Column('document_id', sa.UUID(), nullable=False),
            sa.Column('comments', sa.String(255), nullable=True),
            sa.Column('validation_status', sa.String(20), server_default='CLEAN', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

    # 4. inventory_documents
    if not _table_exists('inventory_documents'):
        op.create_table('inventory_documents',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('folio', sa.String(50), nullable=False),
            sa.Column('document_type', sa.String(20), nullable=False),
            sa.Column('status', postgresql.ENUM(name='documentstatus', create_type=False), server_default='DRAFT', nullable=False),
            sa.Column('origin_name', sa.String(length=255), nullable=True),
            sa.Column('destination_name', sa.String(length=255), nullable=True),
            sa.Column('total_items', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_weight', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('total_amount', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('total_currency', sa.String(3), server_default='USD', nullable=False),
            sa.Column('concept_id', sa.UUID(), nullable=True),
            sa.Column('external_reference', sa.String(100), nullable=False),
            sa.Column('pending_financial_valuation', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('audit_notes', sa.Text(), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('folio'),
            sa.UniqueConstraint('external_reference')
        )

    # 5. inventory_item_variants
    if not _table_exists('inventory_item_variants'):
        op.create_table('inventory_item_variants',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('internal_sku', sa.String(50), nullable=False),
            sa.Column('brand', sa.String(100), nullable=False),
            sa.Column('mfg_part_number', sa.String(100), nullable=False),
            sa.Column('unit_price', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('weight', sa.Numeric(15, 4), nullable=True),
            sa.Column('volume', sa.Numeric(15, 4), nullable=True),
            sa.Column('is_preferred', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('photo_path', sa.String(255), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('company_id', 'internal_sku', 'mfg_part_number', name='uq_variant_per_company')
        )

    # 6. inventory_boms
    if not _table_exists('inventory_boms'):
        op.create_table('inventory_boms',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('uom_id', sa.UUID(), nullable=False),
            sa.Column('component_item_code', sa.String(100), nullable=False),
            sa.Column('quantity', sa.Numeric(14, 4), server_default='1.0', nullable=False),
            sa.Column('uom', sa.String(20), server_default='PCS', nullable=False),
            sa.Column('level', sa.Integer(), server_default='1', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

    # 7. inventory_backflush_errors
    if not _table_exists('inventory_backflush_errors'):
        op.create_table('inventory_backflush_errors',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('event_id', sa.UUID(), nullable=False),
            sa.Column('production_run_id', sa.UUID(), nullable=False),
            sa.Column('warehouse_id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('uom_id', sa.UUID(), nullable=False),
            sa.Column('item_code', sa.String(100), nullable=False),
            sa.Column('required_qty', sa.Numeric(14, 4), nullable=False),
            sa.Column('error_type', postgresql.ENUM(name='backflusherrortype', create_type=False), nullable=False),
            sa.Column('status', postgresql.ENUM(name='backflushstatus', create_type=False), server_default='PENDING', nullable=False),
            *audit_columns,
            sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('error_details', sa.String(255), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 8. customs_pedimentos
    if not _table_exists('customs_pedimentos'):
        op.create_table('customs_pedimentos',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('pedimento_number', sa.String(15), nullable=False),
            sa.Column('customs_key', sa.String(10), nullable=False),
            sa.Column('operation_type', postgresql.ENUM(name='customsoperationtype', create_type=False), nullable=False),
            sa.Column('customs_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_temporary', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('exchange_rate_dof', sa.Numeric(15, 4), nullable=True),
            sa.Column('comments', sa.String(255), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('pedimento_number')
        )

    # 9. inventory_levels
    if not _table_exists('inventory_levels'):
        op.create_table('inventory_levels',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('warehouse_id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('uom_id', sa.UUID(), nullable=False),
            sa.Column('quantity', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('reserved_quantity', sa.Numeric(15, 4), server_default='0', nullable=False),
            sa.Column('wac_amount', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('wac_currency', sa.String(3), server_default='USD', nullable=False),
            sa.Column('last_price_amount', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('last_price_currency', sa.String(3), server_default='USD', nullable=False),
            sa.Column('replacement_price_amount', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('replacement_price_currency', sa.String(3), server_default='USD', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint("company_id", "warehouse_id", "product_id", name="uq_inventory_level_per_company")
        )

    # 10. inventory_transactions
    if not _table_exists('inventory_transactions'):
        op.create_table('inventory_transactions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('warehouse_id', sa.UUID(), nullable=False),
            sa.Column('transaction_type', sa.String(30), nullable=False),
            sa.Column('quantity_change', sa.Numeric(15, 4), nullable=False),
            sa.Column('previous_balance', sa.Numeric(15, 4), nullable=False),
            sa.Column('new_balance', sa.Numeric(15, 4), nullable=False),
            sa.Column('reference_id', sa.UUID(), nullable=True),
            sa.Column('comments', sa.String(255), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

    # 11. inventory_movement_concepts
    if not _table_exists('inventory_movement_concepts'):
        op.create_table('inventory_movement_concepts',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('code', sa.String(50), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('type', sa.String(20), nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

    # 12. inter_company_transfers
    if not _table_exists('inter_company_transfers'):
        op.create_table('inter_company_transfers',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('folio', sa.String(60), nullable=False),
            sa.Column('destination_company_id', sa.UUID(), nullable=False),
            sa.Column('origin_warehouse_id', sa.UUID(), nullable=False),
            sa.Column('destination_warehouse_id', sa.UUID(), nullable=False),
            sa.Column('transit_warehouse_id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('uom_id', sa.UUID(), nullable=False),
            sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
            sa.Column('weight', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('currency', sa.String(3), server_default='USD', nullable=False),
            sa.Column('unit_price_at_dispatch', sa.Numeric(18, 4), server_default='0', nullable=True),
            sa.Column('wac_at_dispatch', sa.Numeric(18, 4), server_default='0', nullable=True),
            sa.Column('transfer_revenue_a', sa.Numeric(18, 4), server_default='0', nullable=True),
            sa.Column('acquisition_cost_b', sa.Numeric(18, 4), server_default='0', nullable=True),
            sa.Column('status', sa.String(20), server_default='PENDING', nullable=False),
            sa.Column('customs_pedimento', sa.String(21), nullable=True),
            sa.Column('customs_pedimento_id', sa.UUID(), nullable=True),
            sa.Column('customs_doc_type', sa.String(20), nullable=True),
            sa.Column('pending_financial_valuation', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('audit_notes', sa.Text(), nullable=True),
            sa.Column('exchange_rate_dof', sa.Numeric(18, 4), nullable=True),
            sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('shipped_by', sa.UUID(), nullable=True),
            sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('received_by', sa.UUID(), nullable=True),
            sa.Column('received_quantity', sa.Numeric(18, 4), nullable=True),
            sa.Column('damaged_quantity', sa.Numeric(18, 4), server_default='0', nullable=True),
            sa.Column('mirror_document_id', sa.UUID(), nullable=True),
            sa.Column('inbound_folio', sa.String(60), nullable=True),
            sa.Column('origin_sku', sa.String(100), nullable=True),
            sa.Column('destination_sku', sa.String(100), nullable=True),
            sa.Column('destination_product_id', sa.UUID(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('external_reference', sa.String(100), nullable=True),
            sa.Column('receive_movement_id', sa.UUID(), nullable=True),
            sa.Column('dispatch_movement_id', sa.UUID(), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('folio')
        )

    # 13. idempotency_keys
    if not _table_exists('idempotency_keys'):
        op.create_table('idempotency_keys',
            sa.Column('key', sa.String(length=255), nullable=False),
            sa.PrimaryKeyConstraint('key')
        )

    # 14. inventory_stocks
    if not _table_exists('inventory_stocks'):
        op.create_table('inventory_stocks',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('warehouse_id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('uom_id', sa.UUID(), nullable=False),
            sa.Column('quantity', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('reserved_quantity', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('min_stock', sa.Numeric(18, 4), server_default='0', nullable=False),
            sa.Column('reorder_point', sa.Numeric(18, 4), server_default='0', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('warehouse_id', 'product_id', 'company_id', name='uq_warehouse_product_tenant')
        )

    # 15. stock_lots
    if not _table_exists('stock_lots'):
        op.create_table('stock_lots',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('product_id', sa.UUID(), nullable=False),
            sa.Column('batch_number', sa.String(length=100), nullable=False),
            sa.Column('expiration_date', sa.Date(), nullable=True),
            sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

def downgrade() -> None:
    pass
