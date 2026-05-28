"""mes: cycle_time_seconds in standard_times + create mes_shifts with break_minutes

Revision ID: 006_mes_cycle_time_and_breaks
Revises: 5e91a2b3c4d5
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006_mes_cycle_time_and_breaks'
down_revision: Union[str, None] = '5e91a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # cycle_time_seconds: machine cycle time per piece in seconds (legacy: OperationTime.RunTime).
    # NULL = not yet time-studied; ManufacturingMath falls back to set_time_hours.
    op.add_column(
        'mes_standard_times',
        sa.Column('cycle_time_seconds', sa.Integer(), nullable=True)
    )

    # mes_shifts: turnos de trabajo. Created here since break_minutes is its initial required column.
    op.create_table(
        'mes_shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_overnight', sa.Boolean(), nullable=False, server_default='false'),
        # break_minutes: total scheduled break per shift (lunch + rest). Default 60 = legacy value.
        sa.Column('break_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['resource_id'], ['mes_resources.id'], name='fk_mes_shifts_resource_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_mes_shifts_code'),
    )
    op.create_index('ix_mes_shifts_code', 'mes_shifts', ['code'], unique=True)
    op.create_index('ix_mes_shifts_company_id', 'mes_shifts', ['company_id'], unique=False)
    op.create_index('ix_mes_shifts_group_id', 'mes_shifts', ['group_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_mes_shifts_group_id', table_name='mes_shifts')
    op.drop_index('ix_mes_shifts_company_id', table_name='mes_shifts')
    op.drop_index('ix_mes_shifts_code', table_name='mes_shifts')
    op.drop_table('mes_shifts')
    op.drop_column('mes_standard_times', 'cycle_time_seconds')
