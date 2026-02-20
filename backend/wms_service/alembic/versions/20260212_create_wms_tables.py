"""create wms tables

Revision ID: wms_init_001
Revises: 
Create Date: 2026-02-12 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'wms_init_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('items',
    sa.Column('master_product_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sku', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('stock_quantity', sa.Float(), nullable=True),
    sa.Column('bin_location', sa.String(length=50), nullable=True),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
    # Se elimina sa.ForeignKeyConstraint para permitir desacoplamiento entre microservicios
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sku', 'company_id', name='_wms_company_sku_uc')
    )
    op.create_index(op.f('ix_items_company_id'), 'items', ['company_id'], unique=False)
    op.create_index(op.f('ix_items_master_product_id'), 'items', ['master_product_id'], unique=False)
    op.create_index(op.f('ix_items_sku'), 'items', ['sku'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_items_sku'), table_name='items')
    op.drop_index(op.f('ix_items_master_product_id'), table_name='items')
    op.drop_index(op.f('ix_items_company_id'), table_name='items')
    op.drop_table('items')