"""create_initial_tables

Revision ID: a302e052fe52
Revises: 
Create Date: 2026-02-17 18:48:14.829199
"""
from alembic import op
import sqlalchemy as sa

revision = 'a302e052fe52'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Tabla de Compañías (Base para Multitenancy)
    op.create_table('companies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Tabla de Unidades de Medida (UOM)
    op.create_table('ums',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'company_id', name='_company_uom_code_uc')
    )

    # 3. Tabla de Categorías
    op.create_table('product_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Tabla de Productos (Interno Core - Clean Architecture)
    op.create_table('products',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('uom_id', sa.UUID(), nullable=True),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('brand_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], ),
        sa.ForeignKeyConstraint(['uom_id'], ['ums.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku', 'company_id', name='_company_product_sku_uc')
    )

def downgrade() -> None:
    op.drop_table('products')
    op.drop_table('product_categories')
    op.drop_table('ums')
    op.drop_table('companies')