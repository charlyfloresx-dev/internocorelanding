"""Add ticket_actions table

Revision ID: 003_add_ticket_actions
Revises: 002_ref_code_composite
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_add_ticket_actions'
down_revision: Union[str, None] = '002_ref_code_composite'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return table in sa_inspect(bind).get_table_names()


def upgrade() -> None:
    if _table_exists('ticket_actions'):
        return

    op.create_table(
        'ticket_actions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('ticket_id', sa.UUID(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('assigned_to_id', sa.UUID(), nullable=True),
        sa.Column('collaborator_id', sa.UUID(), nullable=True),
        sa.Column('external_contact_id', sa.UUID(), nullable=True),
        sa.Column('commit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_closed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], name='fk_ticket_actions_ticket_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ticket_actions_ticket_id', 'ticket_actions', ['ticket_id'])
    op.create_index('ix_ticket_actions_company_id', 'ticket_actions', ['company_id'])
    op.create_index('ix_ticket_actions_assigned_to_id', 'ticket_actions', ['assigned_to_id'])
    op.create_index('ix_ticket_actions_is_closed', 'ticket_actions', ['is_closed'])


def downgrade() -> None:
    if not _table_exists('ticket_actions'):
        return
    op.drop_index('ix_ticket_actions_is_closed', table_name='ticket_actions')
    op.drop_index('ix_ticket_actions_assigned_to_id', table_name='ticket_actions')
    op.drop_index('ix_ticket_actions_company_id', table_name='ticket_actions')
    op.drop_index('ix_ticket_actions_ticket_id', table_name='ticket_actions')
    op.drop_table('ticket_actions')
