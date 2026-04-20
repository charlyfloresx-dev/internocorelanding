"""architecture_cleanup

Revision ID: 99c4ce904b16
Revises: 8eea61ac3409
Create Date: 2026-04-05 16:57:05.136819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99c4ce904b16'
down_revision: Union[str, None] = '8eea61ac3409'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Manual Addition: Create Enums ###
    op.execute("DO $$ BEGIN CREATE TYPE productstatus AS ENUM ('DRAFT', 'ACTIVE', 'INACTIVE', 'DISCONTINUED'); EXCEPTION WHEN duplicate_object THEN null; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE warehousetype AS ENUM ('PHYSICAL', 'VIRTUAL', 'TRANSIT', 'RESOURCE', 'EXT_PARTNER'); EXCEPTION WHEN duplicate_object THEN null; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE movementtype AS ENUM ('ENTRY', 'OUTPUT', 'TRANSFER', 'ADJUSTMENT'); EXCEPTION WHEN duplicate_object THEN null; END $$")

    # --- ITEMS ---
    op.add_column('items', sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'INACTIVE', 'DISCONTINUED', name='productstatus'), server_default='ACTIVE', nullable=False))
    # Fill sku from code if sku is null
    op.execute("UPDATE items SET sku = code WHERE sku IS NULL")
    op.alter_column('items', 'sku', existing_type=sa.String(100), nullable=False)
    op.execute("ALTER TABLE items ADD COLUMN IF NOT EXISTS master_product_id UUID")
    op.execute("ALTER TABLE items ADD COLUMN IF NOT EXISTS sat_product_code VARCHAR(20)")

    # --- WAREHOUSES ---
    op.execute("ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS type warehousetype DEFAULT 'PHYSICAL' NOT NULL")
    op.execute("ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS country_code VARCHAR(2) DEFAULT 'MX' NOT NULL")

    # --- CONCEPTS ---
    op.execute("ALTER TABLE concepts ADD COLUMN IF NOT EXISTS type movementtype")
    op.execute("UPDATE concepts SET type = 'ENTRY' WHERE concept_type = 'ENTRY' AND type IS NULL")
    op.execute("UPDATE concepts SET type = 'OUTPUT' WHERE concept_type = 'OUTPUT' AND type IS NULL")
    op.execute("UPDATE concepts SET type = 'ADJUSTMENT' WHERE concept_type = 'ADJUSTMENT' AND type IS NULL")
    op.execute("UPDATE concepts SET type = 'TRANSFER' WHERE concept_type = 'TRANSFER' AND type IS NULL")
    op.execute("ALTER TABLE concepts ALTER COLUMN type SET NOT NULL")
    # op.drop_column('concepts', 'concept_type')

    # --- TENANT_ID SYNC (MULTI-TENANT BASE FIX) ---
    tables_to_sync = [
        'inventory_documents', 'inventory_movements', 'product_prices', 
        'document_series', 'warehouse_groups', 'warehouse_types', 
        'inventory_snapshots', 'sales_orders', 'file_metadata', 
        'locations', 'warehouse_zones', 'items', 'warehouses', 'concepts'
    ]
    for table in tables_to_sync:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")
        op.execute(f"UPDATE {table} SET tenant_id = company_id WHERE tenant_id IS NULL AND company_id IS NOT NULL")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS version_id INTEGER DEFAULT 1 NOT NULL")

    # 6. IDEMPOTENCY (Necessary for metadata consistency)
    op.execute("""
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key VARCHAR(255) NOT NULL,
            user_id VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (key)
        );
    """)

def downgrade() -> None:
    op.drop_table('idempotency_keys')
    op.drop_column('concepts', 'type')
    op.drop_column('warehouses', 'country_code')
    op.drop_column('warehouses', 'type')
    op.drop_column('items', 'status')
