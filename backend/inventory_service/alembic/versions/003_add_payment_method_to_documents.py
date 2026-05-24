"""add payment_method column to inventory_documents

Revision ID: 003_add_payment_method_to_documents
Revises: 002_drop_inventory_item_variants
Create Date: 2026-05-24

"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_add_payment_method_to_documents'
down_revision: Union[str, None] = '002_drop_inventory_item_variants'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'inventory_documents',
        sa.Column('payment_method', sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('inventory_documents', 'payment_method')
