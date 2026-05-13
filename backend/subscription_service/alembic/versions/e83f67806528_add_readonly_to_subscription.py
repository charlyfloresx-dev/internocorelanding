"""init_subscription_baseline

Revision ID: e83f67806528
Revises: 
Create Date: 2026-03-03 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'e83f67806528'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    # 1. Modules
    if 'modules' not in tables:
        op.create_table(
            'modules',
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('is_core', sa.Boolean(), nullable=False),
            sa.Column('translation_key', sa.String(length=100), nullable=True),
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('code')
        )
        op.create_index(op.f('ix_modules_code'), 'modules', ['code'], unique=True)

    # 2. Plans
    if 'plans' not in tables:
        op.create_table(
            'plans',
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('price', sa.Numeric(precision=18, scale=4), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('trial_days', sa.Integer(), nullable=False),
            sa.Column('storage_limit', sa.BigInteger(), nullable=False),
            sa.Column('allow_overage', sa.Boolean(), nullable=False),
            sa.Column('modules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    # 3. Subscriptions
    if 'subscriptions' not in tables:
        op.create_table(
            'subscriptions',
            sa.Column('plan_id', sa.UUID(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('grace_period_until', sa.DateTime(timezone=True), nullable=True),
            sa.Column('current_storage_usage', sa.BigInteger(), nullable=False),
            sa.Column('readonly', sa.Boolean(), nullable=False),
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('company_id', sa.UUID(), nullable=True),
            sa.Column('tenant_id', sa.UUID(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 4. Entitlements
    if 'entitlements' not in tables:
        op.create_table(
            'entitlements',
            sa.Column('module_code', sa.String(length=50), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('source_subscription_id', sa.UUID(), nullable=True),
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('company_id', sa.UUID(), nullable=True),
            sa.Column('tenant_id', sa.UUID(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['source_subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_entitlements_module_code'), 'entitlements', ['module_code'], unique=False)

    # 5. Logs
    if 'audit_subscription_logs' not in tables:
        op.create_table(
            'audit_subscription_logs',
            sa.Column('subscription_id', sa.UUID(), nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('before_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('after_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('reason', sa.String(length=255), nullable=True),
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('company_id', sa.UUID(), nullable=True),
            sa.Column('tenant_id', sa.UUID(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 6. Billing Events
    if 'billing_events' not in tables:
        op.create_table(
            'billing_events',
            sa.Column('subscription_id', sa.UUID(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=18, scale=4), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('provider_reference', sa.String(length=255), nullable=True),
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('company_id', sa.UUID(), nullable=True),
            sa.Column('tenant_id', sa.UUID(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade() -> None:
    op.drop_table('billing_events')
    op.drop_table('audit_subscription_logs')
    op.drop_index(op.f('ix_entitlements_module_code'), table_name='entitlements')
    op.drop_table('entitlements')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_index(op.f('ix_modules_code'), table_name='modules')
    op.drop_table('modules')

