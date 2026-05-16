"""Subscription Baseline

Revision ID: 000_subscription_baseline
Revises: None
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_subscription_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _table_exists(name):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return name in sa_inspect(bind).get_table_names()

def upgrade() -> None:
    # Helper for Audit + MultiTenant columns
    audit_columns = [
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
    ]
    
    mt_columns = [
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
    ]

    # 1. modules (AuditBase)
    if not _table_exists('modules'):
        op.create_table('modules',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('is_core', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('translation_key', sa.String(length=100), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('code')
        )

    # 2. plans (AuditBase)
    if not _table_exists('plans'):
        op.create_table('plans',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('price', sa.Numeric(precision=18, scale=4), server_default='0.00', nullable=False),
            sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
            sa.Column('trial_days', sa.Integer(), server_default='14', nullable=False),
            sa.Column('storage_limit', sa.BigInteger(), server_default='5368709120', nullable=False),
            sa.Column('allow_overage', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('modules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    # 3. subscriptions (MultiTenantBase)
    if not _table_exists('subscriptions'):
        op.create_table('subscriptions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('plan_id', sa.UUID(), nullable=False),
            sa.Column('status', sa.String(length=20), server_default='TRIAL', nullable=False),
            sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('grace_period_until', sa.DateTime(timezone=True), nullable=True),
            sa.Column('current_storage_usage', sa.BigInteger(), server_default='0', nullable=False),
            sa.Column('readonly', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
            sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
            *mt_columns,
            sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])
        op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])
        op.create_index('ix_subscriptions_company_id', 'subscriptions', ['company_id'])

    # 4. entitlements (MultiTenantBase)
    if not _table_exists('entitlements'):
        op.create_table('entitlements',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('module_code', sa.String(length=50), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('source_subscription_id', sa.UUID(), nullable=True),
            *mt_columns,
            sa.ForeignKeyConstraint(['source_subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_entitlements_module_code', 'entitlements', ['module_code'])
        op.create_index('ix_entitlements_company_id', 'entitlements', ['company_id'])

    # 5. audit_subscription_logs (MultiTenantBase)
    if not _table_exists('audit_subscription_logs'):
        op.create_table('audit_subscription_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('subscription_id', sa.UUID(), nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('before_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('after_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('reason', sa.String(length=255), nullable=True),
            *mt_columns,
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 6. billing_events (MultiTenantBase)
    if not _table_exists('billing_events'):
        op.create_table('billing_events',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('subscription_id', sa.UUID(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=18, scale=4), server_default='0.00', nullable=False),
            sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
            sa.Column('provider', sa.String(length=50), server_default='STRIPE', nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
            sa.Column('provider_reference', sa.String(length=255), nullable=True),
            *mt_columns,
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 7. guest_wallets (AuditBase)
    if not _table_exists('guest_wallets'):
        op.create_table('guest_wallets',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('guest_session_id', sa.String(length=255), nullable=False),
            sa.Column('balance_cents', sa.Integer(), server_default='0', nullable=False),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('guest_session_id')
        )

    # 8. wallet_transactions (AuditBase)
    if not _table_exists('wallet_transactions'):
        op.create_table('wallet_transactions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('guest_wallet_id', sa.UUID(), nullable=False),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('transaction_type', sa.String(length=50), nullable=False),
            sa.Column('reference_id', sa.String(length=255), nullable=True),
            sa.Column('reason', sa.String(length=255), nullable=True),
            *audit_columns,
            sa.ForeignKeyConstraint(['guest_wallet_id'], ['guest_wallets.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade() -> None:
    pass
