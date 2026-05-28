"""inventory: add parent_item_code and is_active to BOM table

Revision ID: 005_add_bom_parent_item_code
Revises: 004_fix_folio_unique_constraint
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa

revision = '005_add_bom_parent_item_code'
down_revision = '004_fix_folio_unique_constraint'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # is_active already existed in the baseline table definition
    op.add_column('inventory_boms', sa.Column('parent_item_code', sa.String(100), nullable=True))
    op.create_index('ix_inventory_boms_parent_item_code', 'inventory_boms', ['parent_item_code'])


def downgrade() -> None:
    op.drop_index('ix_inventory_boms_parent_item_code', table_name='inventory_boms')
    op.drop_column('inventory_boms', 'parent_item_code')
