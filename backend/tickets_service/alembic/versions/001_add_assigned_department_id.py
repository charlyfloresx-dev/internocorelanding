"""Add assigned_department_id to tickets

Revision ID: 001_add_assigned_department_id
Revises: 000_tickets_baseline
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_add_assigned_department_id'
down_revision: Union[str, None] = '000_tickets_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _column_exists(table, column):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    columns = [c['name'] for c in sa_inspect(bind).get_columns(table)]
    return column in columns

def upgrade() -> None:
    if not _column_exists('tickets', 'assigned_department_id'):
        op.add_column('tickets', sa.Column('assigned_department_id', sa.UUID(), nullable=True))
        op.create_index('ix_tickets_assigned_department_id', 'tickets', ['assigned_department_id'])

def downgrade() -> None:
    if _column_exists('tickets', 'assigned_department_id'):
        op.drop_index('ix_tickets_assigned_department_id', 'tickets')
        op.drop_column('tickets', 'assigned_department_id')
