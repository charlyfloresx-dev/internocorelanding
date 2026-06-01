"""drop_legacy_refresh_tokens_table

Revision ID: a9e3b1c0d2f4
Revises: f20a0170fc12
Create Date: 2026-06-01

Depreca la tabla refresh_tokens del esquema stateful (Redis-backed).
Desde Phase 159 RTR Phase D, la familia de tokens RTR (refresh_token_families)
es la única fuente de verdad para refresh tokens.
"""
from alembic import op


revision = 'a9e3b1c0d2f4'
down_revision = 'f20a0170fc12'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('refresh_tokens')


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
