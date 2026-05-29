"""hcm: add hcm_break_groups + hcm_break_slots (Phase 157-HCM)

BreakGroups allow capacity-based break scheduling: each group defines
multiple staggered BreakSlots so that common areas (bathrooms, cafeteria)
are never over-capacity.

Resource.break_group_id in mes_service soft-FKs to hcm_break_groups.id.

Revision ID: 006_add_break_groups
Revises: 005_add_plant_shift_global_entry
Create Date: 2026-05-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006_add_break_groups'
down_revision: Union[str, None] = '005_add_plant_shift_global_entry'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_cols():
    return [
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        'hcm_break_groups',
        *_base_cols(),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(250), nullable=True),
        sa.Column('area_capacity', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_hcm_break_groups_company_id', 'hcm_break_groups', ['company_id'])

    op.create_table(
        'hcm_break_slots',
        *_base_cols(),
        sa.Column('break_group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('label', sa.String(50), nullable=False),
        sa.Column('break_type', sa.String(20), nullable=False, server_default='BREAK'),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('max_concurrent', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(
            ['break_group_id'], ['hcm_break_groups.id'],
            name='fk_hcm_break_slots_group', ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_hcm_break_slots_group_id', 'hcm_break_slots', ['break_group_id'])
    op.create_index('ix_hcm_break_slots_company_id', 'hcm_break_slots', ['company_id'])


def downgrade() -> None:
    op.drop_index('ix_hcm_break_slots_company_id', table_name='hcm_break_slots')
    op.drop_index('ix_hcm_break_slots_group_id', table_name='hcm_break_slots')
    op.drop_table('hcm_break_slots')
    op.drop_index('ix_hcm_break_groups_company_id', table_name='hcm_break_groups')
    op.drop_table('hcm_break_groups')
