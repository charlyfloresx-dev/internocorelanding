"""mes: Facility, ProductionArea, Resource expanded, ResourceSupportMember, ShiftBreak

Revision ID: 009_facility_area_resource
Revises: 008_wo_doc_pattern
Create Date: 2026-05-28

Changes:
  1. Create mes_facilities
  2. Create mes_production_areas
  3. ALTER mes_resources: add description, resource_type, capacity, warehouse_id (soft FK NO CONSTRAINT),
     production_area_id FK, UQ(company_id, code), resize code VARCHAR(13)
  4. Create mes_resource_support_members
  5. Create mes_shift_breaks (portado de HumanResource.Catalog.Break + BreaksGroup)

Note on warehouse_id: intentionally has NO FK constraint — Iron Wall ADR-02.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '009_facility_area_resource'
down_revision: Union[str, None] = '008_wo_doc_pattern'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Columnas base de MultiTenantBase (AuditBase + BaseDomainEntity) — reutilizadas en cada tabla
def _base_cols():
    return [
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
    ]


def upgrade() -> None:
    # ── 1. mes_facilities ─────────────────────────────────────────────────────
    op.create_table(
        'mes_facilities',
        *_base_cols(),
        sa.Column('code', sa.String(25), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('location_description', sa.String(250), nullable=True),
        sa.UniqueConstraint('company_id', 'code', name='uq_facility_company_code'),
    )
    op.create_index('ix_mes_facilities_company_id', 'mes_facilities', ['company_id'])
    op.create_index('ix_mes_facilities_group_id', 'mes_facilities', ['group_id'])

    # ── 2. mes_production_areas ───────────────────────────────────────────────
    op.create_table(
        'mes_production_areas',
        *_base_cols(),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(250), nullable=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('mes_facilities.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('company_id', 'name', 'facility_id', name='uq_area_company_name_facility'),
    )
    op.create_index('ix_mes_production_areas_company_id', 'mes_production_areas', ['company_id'])
    op.create_index('ix_mes_production_areas_facility_id', 'mes_production_areas', ['facility_id'])
    op.create_index('ix_mes_production_areas_group_id', 'mes_production_areas', ['group_id'])

    # ── 3. ALTER mes_resources ────────────────────────────────────────────────
    op.alter_column('mes_resources', 'code', type_=sa.String(13), existing_nullable=False)

    op.add_column('mes_resources', sa.Column('description', sa.String(250), nullable=True))
    op.add_column('mes_resources', sa.Column('resource_type', sa.String(20), nullable=True))
    op.add_column('mes_resources', sa.Column('capacity', sa.Numeric(10, 2), nullable=True))
    op.add_column('mes_resources', sa.Column(
        'warehouse_id', postgresql.UUID(as_uuid=True), nullable=True
    ))  # Intentionally NO FK — Iron Wall ADR-02
    op.add_column('mes_resources', sa.Column(
        'production_area_id', postgresql.UUID(as_uuid=True),
        sa.ForeignKey('mes_production_areas.id', ondelete='SET NULL'), nullable=True
    ))

    op.create_unique_constraint('uq_resource_company_code', 'mes_resources', ['company_id', 'code'])
    op.create_index('ix_mes_resources_resource_type', 'mes_resources', ['resource_type'])
    op.create_index('ix_mes_resources_production_area_id', 'mes_resources', ['production_area_id'])

    # ── 4. mes_resource_support_members ──────────────────────────────────────
    op.create_table(
        'mes_resource_support_members',
        *_base_cols(),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('mes_resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collaborator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
    )
    op.create_index('ix_mes_resource_support_members_resource_id',
                    'mes_resource_support_members', ['resource_id'])
    op.create_index('ix_mes_resource_support_members_company_id',
                    'mes_resource_support_members', ['company_id'])

    # ── 5. mes_shift_breaks ───────────────────────────────────────────────────
    op.create_table(
        'mes_shift_breaks',
        *_base_cols(),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('mes_shifts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(15), nullable=False),
        sa.Column('label', sa.String(50), nullable=False),
        sa.Column('break_type', sa.String(30), nullable=True),
        sa.Column('start_time', sa.Time, nullable=False),
        sa.Column('end_time', sa.Time, nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=False),
    )
    op.create_index('ix_mes_shift_breaks_shift_id', 'mes_shift_breaks', ['shift_id'])
    op.create_index('ix_mes_shift_breaks_company_id', 'mes_shift_breaks', ['company_id'])


def downgrade() -> None:
    op.drop_table('mes_shift_breaks')
    op.drop_table('mes_resource_support_members')

    op.drop_constraint('uq_resource_company_code', 'mes_resources', type_='unique')
    op.drop_index('ix_mes_resources_production_area_id', 'mes_resources')
    op.drop_index('ix_mes_resources_resource_type', 'mes_resources')
    op.drop_column('mes_resources', 'production_area_id')
    op.drop_column('mes_resources', 'warehouse_id')
    op.drop_column('mes_resources', 'capacity')
    op.drop_column('mes_resources', 'resource_type')
    op.drop_column('mes_resources', 'description')
    op.alter_column('mes_resources', 'code', type_=sa.String(50), existing_nullable=False)

    op.drop_table('mes_production_areas')
    op.drop_table('mes_facilities')
