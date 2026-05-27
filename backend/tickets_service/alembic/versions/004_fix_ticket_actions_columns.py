"""Fix ticket_actions missing base columns

Revision ID: 004_fix_ticket_actions_columns
Revises: 003_add_ticket_actions
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_fix_ticket_actions_columns'
down_revision: Union[str, None] = '003_add_ticket_actions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    cols = [c['name'] for c in sa_inspect(bind).get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _column_exists('ticket_actions', 'group_id'):
        op.add_column('ticket_actions', sa.Column('group_id', sa.UUID(), nullable=True))
        op.create_index('ix_ticket_actions_group_id', 'ticket_actions', ['group_id'])

    if not _column_exists('ticket_actions', 'updated_by'):
        op.add_column('ticket_actions', sa.Column('updated_by', sa.UUID(), nullable=True))

    if not _column_exists('ticket_actions', 'deleted_at'):
        op.add_column('ticket_actions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    if not _column_exists('ticket_actions', 'transaction_id'):
        op.add_column('ticket_actions', sa.Column('transaction_id', sa.UUID(), nullable=True))


def downgrade() -> None:
    if _column_exists('ticket_actions', 'transaction_id'):
        op.drop_column('ticket_actions', 'transaction_id')
    if _column_exists('ticket_actions', 'deleted_at'):
        op.drop_column('ticket_actions', 'deleted_at')
    if _column_exists('ticket_actions', 'updated_by'):
        op.drop_column('ticket_actions', 'updated_by')
    if _column_exists('ticket_actions', 'group_id'):
        op.drop_index('ix_ticket_actions_group_id', table_name='ticket_actions')
        op.drop_column('ticket_actions', 'group_id')
