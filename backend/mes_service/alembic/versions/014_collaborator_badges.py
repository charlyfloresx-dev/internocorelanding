"""mes: Phase 170 — CollaboratorBadge table for shop-floor physical authentication

Creates mes_collaborator_badges table for RFID/QR/Barcode HID-mode credentials.
Soft FK to hcm_collaborators (no DB constraint — Iron Wall ADR).

Revision ID: 014_collaborator_badges
Revises: 013_labor_headcount
Create Date: 2026-06-02
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '014_collaborator_badges'
down_revision: Union[str, None] = '013_labor_headcount'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mes_collaborator_badges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),

        # Soft FK — hcm_collaborators lives in hcm_db (Iron Wall ADR)
        sa.Column('collaborator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collaborator_name', sa.String(200), nullable=False),
        sa.Column('employee_number', sa.Integer(), nullable=True),

        sa.Column('badge_raw_value', sa.String(255), nullable=False),
        sa.Column('badge_type', sa.String(20), nullable=False),  # BARCODE | QR | RFID

        # is_active is the MultiTenantBase soft-delete flag (overloaded for badge status)
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),

        sa.UniqueConstraint('badge_raw_value', 'company_id', name='uq_badge_value_company'),
    )
    op.create_index('ix_badge_raw_value', 'mes_collaborator_badges', ['badge_raw_value'])
    op.create_index('ix_badge_collaborator', 'mes_collaborator_badges', ['collaborator_id'])


def downgrade() -> None:
    op.drop_index('ix_badge_collaborator', table_name='mes_collaborator_badges')
    op.drop_index('ix_badge_raw_value', table_name='mes_collaborator_badges')
    op.drop_table('mes_collaborator_badges')
