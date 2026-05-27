"""fix folio unique constraint to be per company_id

Revision ID: 004_fix_folio_unique_constraint
Revises: 003_add_payment_method_to_documents
Create Date: 2026-05-26
"""
from alembic import op

revision = '004_fix_folio_unique_constraint'
down_revision = '003_add_payment_method_to_documents'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('inventory_documents_folio_key', 'inventory_documents', type_='unique')
    op.create_unique_constraint(
        'uq_inventory_documents_folio_per_company',
        'inventory_documents',
        ['company_id', 'folio']
    )


def downgrade():
    op.drop_constraint('uq_inventory_documents_folio_per_company', 'inventory_documents', type_='unique')
    op.create_unique_constraint('inventory_documents_folio_key', 'inventory_documents', ['folio'])
