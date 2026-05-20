"""move inventory_item_variants to master_data_db

Revision ID: 002_add_inventory_item_variants
Revises: df6c_add_currency
Create Date: 2026-05-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002_add_inventory_item_variants'
down_revision: Union[str, None] = 'df6c_add_currency'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    from sqlalchemy import inspect as sa_inspect
    return name in sa_inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _table_exists('inventory_item_variants'):
        return
    op.create_table(
        'inventory_item_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('internal_sku', sa.String(length=50), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=False),
        sa.Column('mfg_part_number', sa.String(length=100), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0'),
        sa.Column('weight', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('volume', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('is_preferred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('photo_path', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'internal_sku', 'mfg_part_number', name='uq_variant_per_company'),
    )
    op.create_index('ix_inventory_item_variants_company_id', 'inventory_item_variants', ['company_id'])
    op.create_index('ix_inventory_item_variants_product_id', 'inventory_item_variants', ['product_id'])
    op.create_index('ix_inventory_item_variants_internal_sku', 'inventory_item_variants', ['internal_sku'])
    op.create_index('ix_inventory_item_variants_mfg_part_number', 'inventory_item_variants', ['mfg_part_number'])


def downgrade() -> None:
    if _table_exists('inventory_item_variants'):
        op.drop_table('inventory_item_variants')
