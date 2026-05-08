"""add_triple_identity_and_audit_columns

Revision ID: c8e7d9b2a1f0
Revises: ba0421906267
Create Date: 2026-05-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'c8e7d9b2a1f0'
down_revision = 'ba0421906267'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Columnas en 'tickets'
    existing_ticket_cols = [c['name'] for c in inspector.get_columns('tickets')]
    if 'external_contact_id' not in existing_ticket_cols:
        op.add_column('tickets', sa.Column('external_contact_id', sa.UUID(), nullable=True))
    if 'collaborator_id' not in existing_ticket_cols:
        op.add_column('tickets', sa.Column('collaborator_id', sa.UUID(), nullable=True))
    if 'is_external' not in existing_ticket_cols:
        op.add_column('tickets', sa.Column('is_external', sa.Boolean(), nullable=False, server_default='false'))
    if 'external_assigned_at' not in existing_ticket_cols:
        op.add_column('tickets', sa.Column('external_assigned_at', sa.DateTime(timezone=True), nullable=True))
    
    # 2. Columnas en 'audit_logs'
    existing_audit_cols = [c['name'] for c in inspector.get_columns('audit_logs')]
    if 'external_contact_id' not in existing_audit_cols:
        op.add_column('audit_logs', sa.Column('external_contact_id', sa.UUID(), nullable=True))
    if 'collaborator_id' not in existing_audit_cols:
        op.add_column('audit_logs', sa.Column('collaborator_id', sa.UUID(), nullable=True))
    
    # 3. Tabla 'external_contacts'
    if 'external_contacts' not in tables:
        op.create_table('external_contacts',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('full_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('company_id', sa.UUID(), nullable=False),
            sa.Column('tenant_id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_external_contacts_email'), 'external_contacts', ['email'], unique=True)
    
    # 4. Tabla 'partner_contacts'
    if 'partner_contacts' not in tables:
        op.create_table('partner_contacts',
            sa.Column('partner_id', sa.UUID(), nullable=False),
            sa.Column('contact_id', sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(['contact_id'], ['external_contacts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('partner_id', 'contact_id')
        )

def downgrade():
    op.drop_table('partner_contacts')
    op.drop_index(op.f('ix_external_contacts_email'), table_name='external_contacts')
    op.drop_table('external_contacts')
    op.drop_column('audit_logs', 'collaborator_id')
    op.drop_column('audit_logs', 'external_contact_id')
    op.drop_column('tickets', 'external_assigned_at')
    op.drop_column('tickets', 'is_external')
    op.drop_column('tickets', 'collaborator_id')
    op.drop_column('tickets', 'external_contact_id')
