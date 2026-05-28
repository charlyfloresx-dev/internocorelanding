"""add_product_scan_patterns

Revision ID: b5c2d3e4f5a6
Revises: a6b1698e23e1
Create Date: 2026-05-28 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'b5c2d3e4f5a6'
down_revision = 'a6b1698e23e1'
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if _table_exists('master_product_scan_patterns'):
        return

    op.create_table(
        'master_product_scan_patterns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        # BaseDomainEntity
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default=sa.text('1')),
        # AuditBase
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', UUID(as_uuid=True), nullable=True),
        # MultiTenantBase
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', UUID(as_uuid=True), nullable=True),
        # Domain fields
        sa.Column('item_code', sa.String(100), nullable=False),
        sa.Column('pattern_name', sa.String(100), nullable=False),
        sa.Column('regex', sa.String(500), nullable=False),
        sa.Column('error_message', sa.String(500), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.UniqueConstraint('company_id', 'item_code', 'pattern_name',
                            name='uq_scan_pattern_company_item_name'),
    )

    op.create_index('ix_scan_patterns_company_item_active',
                    'master_product_scan_patterns',
                    ['company_id', 'item_code', 'is_active'])
    op.create_index('ix_msp_company_id',
                    'master_product_scan_patterns', ['company_id'])
    op.create_index('ix_msp_item_code',
                    'master_product_scan_patterns', ['item_code'])
    op.create_index('ix_msp_tenant_id',
                    'master_product_scan_patterns', ['tenant_id'])


def downgrade():
    op.drop_table('master_product_scan_patterns')
