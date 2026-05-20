"""add_audit_logs to hcm_db

Revision ID: 001_add_audit_logs_hcm
Revises: 000_hcm_baseline
Create Date: 2026-05-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_add_audit_logs_hcm'
down_revision: Union[str, None] = '001_add_id_pattern'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return name in sa_inspect(bind).get_table_names()


def upgrade() -> None:
    if not _table_exists('audit_logs'):
        op.create_table('audit_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('correlation_id', sa.UUID(), nullable=True),
            sa.Column('company_id', sa.UUID(), nullable=True),
            sa.Column('tenant_id', sa.UUID(), nullable=True),
            sa.Column('group_id', sa.UUID(), nullable=True),
            sa.Column('user_id', sa.String(length=100), nullable=True),
            sa.Column('collaborator_id', sa.UUID(), nullable=True),
            sa.Column('external_contact_id', sa.UUID(), nullable=True),
            sa.Column('client_ip', sa.String(length=50), nullable=True),
            sa.Column('user_agent', sa.String(length=255), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('table_name', sa.String(length=100), nullable=True),
            sa.Column('record_id', sa.String(length=100), nullable=True),
            sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.UUID(), nullable=True),
            sa.Column('updated_by', sa.UUID(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('transaction_id', sa.UUID(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
        op.create_index(op.f('ix_audit_logs_company_id'), 'audit_logs', ['company_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_correlation_id'), 'audit_logs', ['correlation_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_group_id'), 'audit_logs', ['group_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_record_id'), 'audit_logs', ['record_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_table_name'), 'audit_logs', ['table_name'], unique=False)
        op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
        op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    if _table_exists('audit_logs'):
        op.drop_table('audit_logs')
