"""schema_sync_base_columns

Syncs all base class columns (BaseDomainEntity, AuditBase, MultiTenantBase,
BaseCatalogEntity, BaseProduct) into WMS tables to prevent UndefinedColumnError.

Revision ID: a1b2c3d4e5f6
Revises: 99c4ce904b16
Create Date: 2026-04-05 18:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '99c4ce904b16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables that inherit from BaseProduct (via BaseCatalogEntity -> MultiTenantBase)
    product_tables = ['items']
    # Tables that inherit from BaseCatalogEntity (warehouses, concepts)
    catalog_tables = ['warehouses', 'concepts']
    # ALL domain tables in WMS
    all_domain_tables = [
        'items', 'warehouses', 'concepts',
        'inventory_documents', 'inventory_movements', 'inventory_snapshots',
        'document_series', 'warehouse_groups', 'warehouse_types',
        'sales_orders', 'locations', 'warehouse_zones', 'product_prices',
    ]

    # --- BaseDomainEntity columns (all domain tables) ---
    for table in all_domain_tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS version_id INTEGER DEFAULT 1 NOT NULL")

    # --- AuditBase columns (all domain tables) ---
    for table in all_domain_tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS created_by UUID")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS updated_by UUID")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS transaction_id UUID")

    # --- MultiTenantBase columns (all domain tables) ---
    for table in all_domain_tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS company_id UUID")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS group_id UUID")

    # --- BaseCatalogEntity columns (items, warehouses, concepts) ---
    for table in catalog_tables + product_tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS code VARCHAR(50)")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS name VARCHAR(255)")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS description TEXT")

    # --- BaseProduct-specific columns (items only) ---
    for table in product_tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS sku VARCHAR(100)")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS sat_product_code VARCHAR(20)")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS master_product_id UUID")

    # --- BaseWarehouse-specific columns (warehouses only) ---
    op.execute("ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS country_code VARCHAR(2) DEFAULT 'MX' NOT NULL")


def downgrade() -> None:
    # Intentionally left empty — these are additive schema changes
    # that match the domain model. Removing them would break the application.
    pass
