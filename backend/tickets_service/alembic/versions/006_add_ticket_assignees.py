"""Add ticket_assignees table

Revision ID: 006_add_ticket_assignees
Revises: 005_fix_ta_nullable
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006_add_ticket_assignees'
down_revision: Union[str, None] = '005_fix_ta_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return table in sa_inspect(bind).get_table_names()


def upgrade() -> None:
    if _table_exists('ticket_assignees'):
        return

    op.create_table(
        'ticket_assignees',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('ticket_id', sa.UUID(), nullable=False),
        sa.Column('identity_type', sa.String(20), nullable=False),
        sa.Column('identity_id', sa.UUID(), nullable=False),
        sa.Column('is_lead', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('assigned_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], name='fk_ticket_assignees_ticket_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ticket_assignees_ticket_id', 'ticket_assignees', ['ticket_id'])
    op.create_index('ix_ticket_assignees_company_id', 'ticket_assignees', ['company_id'])
    op.create_index('ix_ticket_assignees_identity_id', 'ticket_assignees', ['identity_id'])
    op.create_index('ix_ticket_assignees_type', 'ticket_assignees', ['identity_type'])

    # Backfill desde las 3 columnas legacy
    op.execute("""
        INSERT INTO ticket_assignees (id, company_id, tenant_id, ticket_id, identity_type, identity_id, is_lead, assigned_at, is_active, version_id)
        SELECT gen_random_uuid(), company_id, tenant_id, id, 'INTERNAL', assigned_to_id, true, COALESCE(updated_at, created_at), true, 1
        FROM tickets
        WHERE assigned_to_id IS NOT NULL AND is_active = true
    """)
    op.execute("""
        INSERT INTO ticket_assignees (id, company_id, tenant_id, ticket_id, identity_type, identity_id, is_lead, assigned_at, is_active, version_id)
        SELECT gen_random_uuid(), company_id, tenant_id, id, 'PLANTA', collaborator_id, false, COALESCE(updated_at, created_at), true, 1
        FROM tickets
        WHERE collaborator_id IS NOT NULL AND is_active = true
    """)
    op.execute("""
        INSERT INTO ticket_assignees (id, company_id, tenant_id, ticket_id, identity_type, identity_id, is_lead, assigned_at, is_active, version_id)
        SELECT gen_random_uuid(), company_id, tenant_id, id, 'EXTERNO', external_contact_id, false, COALESCE(updated_at, created_at), true, 1
        FROM tickets
        WHERE external_contact_id IS NOT NULL AND is_active = true
    """)


def downgrade() -> None:
    if not _table_exists('ticket_assignees'):
        return
    op.drop_index('ix_ticket_assignees_type', table_name='ticket_assignees')
    op.drop_index('ix_ticket_assignees_identity_id', table_name='ticket_assignees')
    op.drop_index('ix_ticket_assignees_company_id', table_name='ticket_assignees')
    op.drop_index('ix_ticket_assignees_ticket_id', table_name='ticket_assignees')
    op.drop_table('ticket_assignees')
