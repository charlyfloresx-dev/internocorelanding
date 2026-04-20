"""create collaborators table

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-04-14 00:00:00.000000

INDUSTRIAL UPDATE: 
  - internal_id: String(50) for alphanumeric IDs
  - Added: Collaborators.department, Collaborators.translation_key
  - Added: hr_tenant_configs (including is_active)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Collaborators table ──
    op.create_table(
        'collaborators',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('internal_id', sa.String(50), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('department', sa.String(50), nullable=True),
        sa.Column('translation_key', sa.String(100), nullable=True),
        sa.Column('is_direct', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('home_warehouse_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('supervisor_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('rfid_tag', sa.String(64), nullable=True),
        sa.Column('pin_code', sa.String(128), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('company_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['supervisor_id'], ['collaborators.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('internal_id', 'company_id', name='uq_collaborator_internal_id_company'),
    )
    op.create_index('ix_collaborators_company_id', 'collaborators', ['company_id'])
    op.create_index('ix_collaborators_department', 'collaborators', ['department'])
    op.create_index('ix_collaborator_rfid_company', 'collaborators', ['rfid_tag', 'company_id'])

    # ── hr_tenant_configs ──
    op.create_table(
        'hr_tenant_configs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('internal_id_pattern', sa.String(255), nullable=True),
        sa.Column('pattern_error_message', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('company_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('company_id', name='uq_hr_tenant_config_company'),
    )
    op.create_index('ix_hr_tenant_configs_company_id', 'hr_tenant_configs', ['company_id'])


def downgrade() -> None:
    op.drop_table('hr_tenant_configs')
    op.drop_table('collaborators')
