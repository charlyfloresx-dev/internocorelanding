"""Phase 50: Collaborator identity expansion
- Cross-border credentials (visa, sentry, license + expiry dates)
- Fiscal identity (RFC, CURP, NSS) with legacy .NET constraints
- Industrial safety fields (HazMat, medical cert, drug test, blood type)
- Emergency contact as JSONB with standardized schema
- ERP bridge: m3_operator_id
- Job title field

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 19:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ERP integration ────────────────────────────────────────────────────────
    op.add_column('collaborators', sa.Column('m3_operator_id', sa.String(30), nullable=True))
    op.add_column('collaborators', sa.Column('job_title', sa.String(100), nullable=True))

    # ── Fiscal Identity (Mexico) ───────────────────────────────────────────────
    # Values validated via Pydantic regex before reaching the DB.
    op.add_column('collaborators', sa.Column('rfc', sa.String(13), nullable=True))
    op.add_column('collaborators', sa.Column('curp', sa.String(18), nullable=True))
    op.add_column('collaborators', sa.Column('nss', sa.String(11), nullable=True))

    # ── Cross-Border Credentials ───────────────────────────────────────────────
    # Date (not DateTime) to avoid timezone conflicts in day-level expiry checks.
    op.add_column('collaborators', sa.Column('visa_number', sa.String(20), nullable=True))
    op.add_column('collaborators', sa.Column('visa_expiry', sa.Date(), nullable=True))
    op.add_column('collaborators', sa.Column('sentry_id', sa.String(30), nullable=True))
    op.add_column('collaborators', sa.Column('driver_license_number', sa.String(30), nullable=True))
    op.add_column('collaborators', sa.Column('driver_license_expiry', sa.Date(), nullable=True))

    # ── HazMat & Medical Compliance (SCT/DOT) ─────────────────────────────────
    op.add_column('collaborators', sa.Column(
        'hazardous_material_certified', sa.Boolean(), nullable=False, server_default='false'
    ))
    op.add_column('collaborators', sa.Column('medical_certificate_expiry', sa.Date(), nullable=True))
    op.add_column('collaborators', sa.Column('last_drug_test_date', sa.Date(), nullable=True))

    # ── Industrial Safety ──────────────────────────────────────────────────────
    op.add_column('collaborators', sa.Column('blood_type', sa.String(5), nullable=True))
    op.add_column('collaborators', sa.Column(
        'emergency_contact',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
        comment='Schema: {name, relationship, phone, alternative_phone}'
    ))

    # ── New Indexes ────────────────────────────────────────────────────────────
    # M3 operator ID scoped by tenant for ERP lookups
    op.create_index('ix_collaborator_m3_company', 'collaborators', ['m3_operator_id', 'company_id'])


def downgrade() -> None:
    op.drop_index('ix_collaborator_m3_company', table_name='collaborators')

    # Drop in reverse order of creation
    op.drop_column('collaborators', 'emergency_contact')
    op.drop_column('collaborators', 'blood_type')
    op.drop_column('collaborators', 'last_drug_test_date')
    op.drop_column('collaborators', 'medical_certificate_expiry')
    op.drop_column('collaborators', 'hazardous_material_certified')
    op.drop_column('collaborators', 'driver_license_expiry')
    op.drop_column('collaborators', 'driver_license_number')
    op.drop_column('collaborators', 'sentry_id')
    op.drop_column('collaborators', 'visa_expiry')
    op.drop_column('collaborators', 'visa_number')
    op.drop_column('collaborators', 'nss')
    op.drop_column('collaborators', 'curp')
    op.drop_column('collaborators', 'rfc')
    op.drop_column('collaborators', 'job_title')
    op.drop_column('collaborators', 'm3_operator_id')
