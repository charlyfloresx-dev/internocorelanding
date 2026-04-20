"""add_price_agreements_immutable

Revision ID: cbe35341e931
Revises: (previous)
Create Date: 2026-04-13

NOTE: This hand-curated migration ONLY creates the price_agreements table.
      The autogenerate output for audit_logs changes was intentionally removed
      to avoid runtime cast errors on existing data.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'cbe35341e931'
down_revision = '87e06c6c460a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'price_agreements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Business columns
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(12, 4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='MXN'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('document_reference', sa.String(250), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='MANUAL'),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_price_agreements_company_id',   'price_agreements', ['company_id'])
    op.create_index('ix_price_agreements_tenant_id',    'price_agreements', ['tenant_id'])
    op.create_index('ix_price_agreements_group_id',     'price_agreements', ['group_id'])
    op.create_index('ix_price_agreements_product_id',   'price_agreements', ['product_id'])
    op.create_index('ix_price_agreements_partner_id',   'price_agreements', ['partner_id'])
    # Partial index: fast lookup of the active price per (product, partner, currency)
    op.execute(
        "CREATE INDEX ix_price_agreements_active ON price_agreements (product_id, partner_id, currency) "
        "WHERE valid_until IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_price_agreements_active")
    op.drop_index('ix_price_agreements_partner_id',  'price_agreements')
    op.drop_index('ix_price_agreements_product_id',  'price_agreements')
    op.drop_index('ix_price_agreements_group_id',    'price_agreements')
    op.drop_index('ix_price_agreements_tenant_id',   'price_agreements')
    op.drop_index('ix_price_agreements_company_id',  'price_agreements')
    op.drop_table('price_agreements')
