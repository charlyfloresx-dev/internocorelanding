"""refresh_token_multitenant: Add tenant_id and group_id to refresh_tokens

This migration promotes the RefreshToken model from AuditBase
to MultiTenantBase compliance by adding the two missing columns:
  - tenant_id: enforces tenant-level data isolation at the DB row level.
  - group_id:  enables optional business-group scoping (nullable).

Revision ID: b3e1f9d0a14c
Revises: 6951cac9a0d8
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3e1f9d0a14c'
down_revision = '6951cac9a0d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tenant_id: mirrors company_id for Zero-Trust row-level isolation.
    # Seeded as a copy of company_id for all existing rows via server_default.
    op.add_column(
        'refresh_tokens',
        sa.Column('tenant_id', sa.UUID(), nullable=True)
    )
    # Back-fill existing rows: tenant = company for auth tokens
    op.execute("UPDATE refresh_tokens SET tenant_id = company_id WHERE tenant_id IS NULL")
    # Enforce NOT NULL after back-fill
    op.alter_column('refresh_tokens', 'tenant_id', nullable=False)
    op.create_index(
        op.f('ix_refresh_tokens_tenant_id'),
        'refresh_tokens',
        ['tenant_id'],
        unique=False
    )

    # group_id: optional business-group scoping (nullable is correct)
    op.add_column(
        'refresh_tokens',
        sa.Column('group_id', sa.UUID(), nullable=True)
    )
    op.create_index(
        op.f('ix_refresh_tokens_group_id'),
        'refresh_tokens',
        ['group_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_group_id'), table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'group_id')

    op.drop_index(op.f('ix_refresh_tokens_tenant_id'), table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'tenant_id')
