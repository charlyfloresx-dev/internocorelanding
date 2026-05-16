"""Tickets Baseline

Revision ID: 000_tickets_baseline
Revises: None
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_tickets_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _table_exists(name):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    return name in sa_inspect(bind).get_table_names()

def _type_exists(name):
    bind = op.get_bind()
    res = bind.execute(sa.text(f"SELECT 1 FROM pg_type WHERE typname = '{name}'"))
    return res.first() is not None

def upgrade() -> None:
    # 0. Create ENUMs
    if not _type_exists('ticketstatus'):
        postgresql.ENUM('Nuevo', 'Pendiente de Aprobaci\u00f3n', 'En revisi\u00f3n', 'Asignado', 'En progreso', 'En espera', 'Resuelto', 'Cerrado', 'Cancelado', name='ticketstatus').create(op.get_bind())
    
    if not _type_exists('ticketpriority'):
        postgresql.ENUM('Baja', 'Media', 'Alta', 'Cr\u00edtica', name='ticketpriority').create(op.get_bind())
    
    if not _type_exists('tickettype'):
        postgresql.ENUM('Soporte', 'Incidencia', 'Mejora', 'Queja', 'Tarea', 'Mantenimiento', 'Recibo Material', 'Tiempo Muerto', 'Escalaci\u00f3n', name='tickettype').create(op.get_bind())

    # Helper for Audit + MultiTenant columns
    audit_columns = [
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
    ]

    # 1. tickets
    if not _table_exists('tickets'):
        op.create_table('tickets',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('reference_code', sa.String(length=20), nullable=False),
            sa.Column('title', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('ticket_type', postgresql.ENUM(name='tickettype', create_type=False), server_default='Soporte', nullable=False),
            sa.Column('priority', postgresql.ENUM(name='ticketpriority', create_type=False), server_default='Media', nullable=False),
            sa.Column('status', postgresql.ENUM(name='ticketstatus', create_type=False), server_default='Nuevo', nullable=False),
            sa.Column('assigned_to_id', sa.UUID(), nullable=True),
            sa.Column('collaborator_id', sa.UUID(), nullable=True),
            sa.Column('external_contact_id', sa.UUID(), nullable=True),
            sa.Column('external_assigned_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deduplication_hash', sa.String(length=64), nullable=True),
            sa.Column('external_token', sa.String(length=64), nullable=True),
            sa.Column('module_origin', sa.String(length=50), nullable=True),
            sa.Column('area', sa.String(length=100), nullable=True),
            sa.Column('estimated_time', sa.Integer(), nullable=True),
            sa.Column('real_time_spent', sa.Integer(), nullable=True),
            sa.Column('cost_estimate', sa.Numeric(precision=18, scale=8), nullable=True),
            sa.Column('source_service', sa.String(length=50), nullable=True),
            sa.Column('station_id', sa.UUID(), nullable=True),
            sa.Column('reported_by_id', sa.UUID(), nullable=True),
            sa.Column('parent_ticket_id', sa.UUID(), nullable=True),
            sa.Column('auto_close_on_event', sa.String(length=100), nullable=True),
            sa.Column('escalation_level', sa.Integer(), server_default='0', nullable=False),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            *audit_columns,
            sa.ForeignKeyConstraint(['parent_ticket_id'], ['tickets.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('reference_code')
        )
        op.create_index('ix_tickets_reference_code', 'tickets', ['reference_code'])
        op.create_index('ix_tickets_company_id', 'tickets', ['company_id'])

    # 2. ticket_comments
    if not _table_exists('ticket_comments'):
        op.create_table('ticket_comments',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('ticket_id', sa.UUID(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('author_id', sa.UUID(), nullable=False),
            *audit_columns,
            sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id']),
            sa.PrimaryKeyConstraint('id')
        )

    # 3. ticket_history
    if not _table_exists('ticket_history'):
        op.create_table('ticket_history',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('ticket_id', sa.UUID(), nullable=False),
            sa.Column('change_type', sa.String(length=50), nullable=False),
            sa.Column('old_value', sa.String(length=100), nullable=True),
            sa.Column('new_value', sa.String(length=100), nullable=True),
            sa.Column('changed_by_id', sa.UUID(), nullable=False),
            *audit_columns,
            sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id']),
            sa.PrimaryKeyConstraint('id')
        )

    # 4. ticket_resources
    if not _table_exists('ticket_resources'):
        op.create_table('ticket_resources',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('ticket_id', sa.UUID(), nullable=False),
            sa.Column('resource_id', sa.UUID(), nullable=False),
            sa.Column('quantity', sa.Numeric(18, 8), nullable=False),
            *audit_columns,
            sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 5. ticket_stop_logs
    if not _table_exists('ticket_stop_logs'):
        op.create_table('ticket_stop_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('ticket_id', sa.UUID(), nullable=False),
            sa.Column('station_id', sa.UUID(), nullable=False),
            sa.Column('downtime_minutes', sa.Integer(), nullable=False),
            *audit_columns,
            sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 6. outbox_events
    if not _table_exists('outbox_events'):
        op.create_table('outbox_events',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('event_id', sa.UUID(), nullable=False),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('payload', sa.Text(), nullable=False),
            sa.Column('is_processed', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_id')
        )

    # 7. escalation_rules
    if not _table_exists('escalation_rules'):
        op.create_table('escalation_rules',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('area', sa.String(length=50), nullable=False),
            sa.Column('level', sa.Integer(), nullable=False),
            sa.Column('role_name', sa.String(length=100), nullable=False),
            sa.Column('sla_minutes', sa.Integer(), nullable=False),
            sa.Column('notification_channel', sa.String(length=20), server_default='PUSH', nullable=True),
            *audit_columns,
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('company_id', 'area', 'level', name='uq_company_area_level')
        )

def downgrade() -> None:
    pass
