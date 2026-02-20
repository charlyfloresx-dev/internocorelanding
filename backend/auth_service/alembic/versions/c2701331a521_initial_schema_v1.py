"""initial_schema_v1
Revision ID: c2701331a521
Revises: 
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c2701331a521'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Columnas de auditoría reusables
    audit_cols = [
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('version_id', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
    ]

    # 1. Companies
    op.create_table('companies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('tax_id', sa.String(), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('logo', sa.String(), nullable=True),
        *audit_cols,
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Users
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        *audit_cols,
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', 'company_id', name='uq_user_email_company')
    )

    # 3. Roles
    op.create_table('roles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        *audit_cols,
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 4. Permissions
    op.create_table('permissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        *audit_cols,
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 5. Role-Permission Intermedia
    op.create_table('role_permissions',
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('permission_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 6. User-Company-Role (Identidad Triple con Auditoría)
    op.create_table('user_company_roles',
        sa.Column('id', sa.UUID(), nullable=False), # BaseEntity requiere ID
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('is_new', sa.Boolean(), server_default='true'),
        sa.Column('scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *audit_cols,
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id', 'company_id', 'role_id')
    )

def downgrade() -> None:
    op.drop_table('user_company_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('companies')