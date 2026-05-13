"""Init

Revision ID: d53275884ee8
Revises: 
Create Date: 2026-04-30 18:14:16.680734

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd53275884ee8'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(name):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return name in sa_inspect(bind).get_table_names()


def _safe_index(index_name, table_name, columns, **kwargs):
    try:
        op.create_index(index_name, table_name, columns, **kwargs)
    except Exception:
        pass


def upgrade():
    if not _table_exists('audit_logs'):
        op.create_table('audit_logs',
        sa.Column('correlation_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('collaborator_id', sa.UUID(), nullable=True),
        sa.Column('external_contact_id', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'])
        _safe_index(op.f('ix_audit_logs_company_id'), 'audit_logs', ['company_id'])
        _safe_index(op.f('ix_audit_logs_correlation_id'), 'audit_logs', ['correlation_id'])
        _safe_index(op.f('ix_audit_logs_group_id'), 'audit_logs', ['group_id'])
        _safe_index(op.f('ix_audit_logs_record_id'), 'audit_logs', ['record_id'])
        _safe_index(op.f('ix_audit_logs_table_name'), 'audit_logs', ['table_name'])
        _safe_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'])
        _safe_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'])
        _safe_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'])

    if not _table_exists('business_groups'):
        op.create_table('business_groups',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_business_groups_name'), 'business_groups', ['name'])

    if not _table_exists('file_metadata'):
        op.create_table('file_metadata',
        sa.Column('bucket', sa.String(length=255), nullable=False),
        sa.Column('key', sa.String(length=500), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('original_name', sa.String(length=255), nullable=True),
        sa.Column('service_source', sa.String(length=50), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_file_metadata_company_id'), 'file_metadata', ['company_id'])
        _safe_index(op.f('ix_file_metadata_group_id'), 'file_metadata', ['group_id'])
        _safe_index(op.f('ix_file_metadata_key'), 'file_metadata', ['key'])
        _safe_index(op.f('ix_file_metadata_tenant_id'), 'file_metadata', ['tenant_id'])

    if not _table_exists('idempotency_keys'):
        op.create_table('idempotency_keys',
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('key')
        )

    if not _table_exists('permissions'):
        op.create_table('permissions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('module_name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'company_id', name='uq_permission_name_company'),
        sa.UniqueConstraint('slug')
        )
        _safe_index(op.f('ix_permissions_company_id'), 'permissions', ['company_id'])
        _safe_index(op.f('ix_permissions_group_id'), 'permissions', ['group_id'])
        _safe_index(op.f('ix_permissions_tenant_id'), 'permissions', ['tenant_id'])

    if not _table_exists('roles'):
        op.create_table('roles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('is_system_role', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'company_id', name='uq_role_name_company')
        )
        _safe_index(op.f('ix_roles_company_id'), 'roles', ['company_id'])
        _safe_index(op.f('ix_roles_group_id'), 'roles', ['group_id'])
        _safe_index(op.f('ix_roles_tenant_id'), 'roles', ['tenant_id'])

    if not _table_exists('users'):
        op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name_pat', sa.String(length=100), nullable=True),
        sa.Column('last_name_mat', sa.String(length=100), nullable=True),
        sa.Column('rfc', sa.String(length=50), nullable=True),
        sa.Column('curp', sa.String(length=50), nullable=True),
        sa.Column('visa_number', sa.String(length=50), nullable=True),
        sa.Column('sentry_id', sa.String(length=50), nullable=True),
        sa.Column('is_biometric_enabled', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_users_curp'), 'users', ['curp'])
        _safe_index(op.f('ix_users_rfc'), 'users', ['rfc'])

    if not _table_exists('companies'):
        op.create_table('companies',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('logo', sa.String(length=500), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('parent_group_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('base_currency', sa.String(length=3), nullable=False),
        sa.Column('default_tax_rate', sa.Numeric(5, 4), server_default='0.16', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['parent_group_id'], ['business_groups.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_companies_parent_group_id'), 'companies', ['parent_group_id'])

    if not _table_exists('refresh_tokens'):
        op.create_table('refresh_tokens',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_refresh_tokens_company_id'), 'refresh_tokens', ['company_id'])
        _safe_index(op.f('ix_refresh_tokens_group_id'), 'refresh_tokens', ['group_id'])
        _safe_index(op.f('ix_refresh_tokens_tenant_id'), 'refresh_tokens', ['tenant_id'])
        _safe_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
        _safe_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'])

    if not _table_exists('role_permissions'):
        op.create_table('role_permissions',
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('permission_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id', 'id')
        )
        _safe_index(op.f('ix_role_permissions_company_id'), 'role_permissions', ['company_id'])
        _safe_index(op.f('ix_role_permissions_group_id'), 'role_permissions', ['group_id'])
        _safe_index(op.f('ix_role_permissions_tenant_id'), 'role_permissions', ['tenant_id'])

    if not _table_exists('user_credentials'):
        op.create_table('user_credentials',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('credential_type', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('public_key', postgresql.BYTEA(), nullable=True),
        sa.Column('device_fingerprint', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_user_credentials_email'), 'user_credentials', ['email'], unique=True)
        _safe_index(op.f('ix_user_credentials_user_id'), 'user_credentials', ['user_id'])

    if not _table_exists('invitations'):
        op.create_table('invitations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=8), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        _safe_index(op.f('ix_invitations_code'), 'invitations', ['code'], unique=True)
        _safe_index(op.f('ix_invitations_email'), 'invitations', ['email'])
        _safe_index(op.f('ix_invitations_group_id'), 'invitations', ['group_id'])
        _safe_index(op.f('ix_invitations_tenant_id'), 'invitations', ['tenant_id'])

    if not _table_exists('user_company_roles'):
        op.create_table('user_company_roles',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('is_new', sa.Boolean(), nullable=False),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'company_id', 'role_id', 'id')
        )
        _safe_index(op.f('ix_user_company_roles_company_id'), 'user_company_roles', ['company_id'])
        _safe_index(op.f('ix_user_company_roles_group_id'), 'user_company_roles', ['group_id'])
        _safe_index(op.f('ix_user_company_roles_tenant_id'), 'user_company_roles', ['tenant_id'])

    if not _table_exists('enumerations'):
        op.create_table('enumerations',
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('translation_key', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type', 'key', 'company_id', name='uq_enum_type_key_company')
        )
        _safe_index(op.f('ix_enumerations_company_id'), 'enumerations', ['company_id'])
        _safe_index(op.f('ix_enumerations_tenant_id'), 'enumerations', ['tenant_id'])
        _safe_index(op.f('ix_enumerations_key'), 'enumerations', ['key'])
        _safe_index(op.f('ix_enumerations_type'), 'enumerations', ['type'])
        _safe_index('ix_enumerations_type_company_active', 'enumerations', ['type', 'company_id', 'is_active'])

    if not _table_exists('security_audit_logs'):
        op.create_table('security_audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('collaborator_id', sa.UUID(), nullable=True),
        sa.Column('access_method', sa.String(length=50), nullable=True),
        sa.Column('identity_identifier', sa.String(length=255), nullable=True),
        sa.Column('roles_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scopes_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('terminal_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
        )

    if not _table_exists('external_contacts'):
        op.create_table('external_contacts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('job_title', sa.String(length=100), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    tables = [
        'external_contacts', 'security_audit_logs', 'enumerations',
        'user_company_roles', 'invitations', 'user_credentials',
        'role_permissions', 'refresh_tokens', 'companies',
        'users', 'roles', 'permissions', 'idempotency_keys',
        'file_metadata', 'business_groups', 'audit_logs'
    ]
    for t in tables:
        try:
            op.drop_table(t)
        except Exception:
            pass
    # ### end Alembic commands ###