"""hcm_baseline

Revision ID: 000_hcm_baseline
Revises: None
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_hcm_baseline'
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

    # 1. collaborators
    if not _table_exists('collaborators'):
        op.create_table('collaborators',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('internal_id', sa.String(length=50), nullable=False),
            sa.Column('first_name', sa.String(length=100), nullable=False),
            sa.Column('last_name', sa.String(length=100), nullable=False),
            sa.Column('department', sa.String(length=50), nullable=True),
            sa.Column('job_title', sa.String(length=100), nullable=True),
            sa.Column('is_direct', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('home_warehouse_id', sa.UUID(), nullable=True),
            sa.Column('supervisor_id', sa.UUID(), nullable=True),
            sa.Column('rfid_tag', sa.String(length=64), nullable=True),
            sa.Column('pin_code', sa.String(length=128), nullable=True),
            sa.Column('m3_operator_id', sa.String(length=30), nullable=True),
            sa.Column('rfc', sa.String(length=13), nullable=True),
            sa.Column('curp', sa.String(length=18), nullable=True),
            sa.Column('nss', sa.String(length=11), nullable=True),
            sa.Column('visa_number', sa.String(length=20), nullable=True),
            sa.Column('visa_expiry', sa.Date(), nullable=True),
            sa.Column('sentry_id', sa.String(length=30), nullable=True),
            sa.Column('driver_license_number', sa.String(length=30), nullable=True),
            sa.Column('driver_license_expiry', sa.Date(), nullable=True),
            sa.Column('hazardous_material_certified', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('medical_certificate_expiry', sa.Date(), nullable=True),
            sa.Column('last_drug_test_date', sa.Date(), nullable=True),
            sa.Column('blood_type', sa.String(length=5), nullable=True),
            sa.Column('photo_path', sa.String(length=255), nullable=True),
            sa.Column('user_id', sa.UUID(), nullable=True),
            sa.Column('emergency_contact', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            *audit_columns,
            sa.ForeignKeyConstraint(['supervisor_id'], ['collaborators.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('internal_id', 'company_id', name='uq_collaborator_internal_id_company')
        )
        op.create_index('ix_collaborator_rfid_company', 'collaborators', ['rfid_tag', 'company_id'])
        op.create_index('ix_collaborator_m3_company', 'collaborators', ['m3_operator_id', 'company_id'])

    # 2. hr_tenant_configs
    if not _table_exists('hr_tenant_configs'):
        op.create_table('hr_tenant_configs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('payroll_frequency', sa.String(length=20), server_default='WEEKLY', nullable=False),
            sa.Column('overtime_policy', sa.String(length=50), server_default='STANDARD', nullable=False),
            sa.Column('shift_schedules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

    # 3. external_contacts (Shared/Triple Identity)
    if not _table_exists('external_contacts'):
        op.create_table('external_contacts',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('full_name', sa.String(length=200), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('job_title', sa.String(length=100), nullable=True),
            sa.Column('department', sa.String(length=100), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id')
        )

def downgrade() -> None:
    pass
