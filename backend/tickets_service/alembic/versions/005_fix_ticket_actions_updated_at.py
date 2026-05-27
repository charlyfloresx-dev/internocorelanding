"""Fix ticket_actions updated_at nullable

Revision ID: 005_fix_ticket_actions_updated_at
Revises: 004_fix_ticket_actions_columns
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_fix_ta_nullable'
down_revision: Union[str, None] = '004_fix_ticket_actions_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'ticket_actions', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None
    )


def downgrade() -> None:
    op.alter_column(
        'ticket_actions', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('now()')
    )
