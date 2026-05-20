"""add currency exchange rates table

Revision ID: df6c_add_currency
Revises: f21020a05ace
Create Date: 2026-05-16 09:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'df6c_add_currency'
down_revision = 'f21020a05ace'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'currency_exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('base_currency', sa.String(length=3), nullable=False),
        sa.Column('target_currency', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('captured_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # Compound index for lookup performance
    op.create_index('ix_cer_lookup', 'currency_exchange_rates', ['company_id', 'base_currency', 'target_currency', sa.text('captured_at DESC')], unique=False)
    op.create_index(op.f('ix_currency_exchange_rates_company_id'), 'currency_exchange_rates', ['company_id'], unique=False)
    op.create_index(op.f('ix_currency_exchange_rates_tenant_id'), 'currency_exchange_rates', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_currency_exchange_rates_group_id'), 'currency_exchange_rates', ['group_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_currency_exchange_rates_group_id'), table_name='currency_exchange_rates')
    op.drop_index(op.f('ix_currency_exchange_rates_tenant_id'), table_name='currency_exchange_rates')
    op.drop_index(op.f('ix_currency_exchange_rates_company_id'), table_name='currency_exchange_rates')
    op.drop_index('ix_cer_lookup', table_name='currency_exchange_rates')
    op.drop_table('currency_exchange_rates')
