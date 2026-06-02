"""mes: Phase 171 fix — add missing MultiTenantBase columns to 013/014 tables

Migration 013 (mes_hourly_labor_snapshots) and 014 (mes_collaborator_badges)
were created without group_id, updated_by, deleted_at, transaction_id that
MultiTenantBase.AuditBase declares. SQLAlchemy SELECT includes all mapped columns
causing UndefinedColumnError at runtime.

Revision ID: 015_fix_base_columns
Revises: 014_collaborator_badges
Create Date: 2026-06-02
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '015_fix_base_columns'
down_revision: Union[str, None] = '014_collaborator_badges'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ['mes_hourly_labor_snapshots', 'mes_collaborator_badges']

_COLS = [
    ('group_id',       postgresql.UUID(as_uuid=True), True,  None),
    ('updated_by',     postgresql.UUID(as_uuid=True), True,  None),
    ('deleted_at',     sa.DateTime(timezone=True),     True,  None),
    ('transaction_id', postgresql.UUID(as_uuid=True), True,  None),
]


def upgrade() -> None:
    for table in _TABLES:
        for col_name, col_type, nullable, server_default in _COLS:
            op.add_column(
                table,
                sa.Column(col_name, col_type, nullable=nullable, server_default=server_default),
            )
        op.create_index(f'ix_{table}_group_id', table, ['group_id'])


def downgrade() -> None:
    for table in _TABLES:
        op.drop_index(f'ix_{table}_group_id', table_name=table)
        for col_name, *_ in _COLS:
            op.drop_column(table, col_name)
