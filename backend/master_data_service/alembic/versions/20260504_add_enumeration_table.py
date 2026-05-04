"""add enumeration table

Revision ID: b45c9a28e3a1
Revises: 
Create Date: 2026-05-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b45c9a28e3a1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('enumerations',
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('translation_key', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        
        # MultiTenantBase fields
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type', 'key', 'company_id', name='uq_enum_type_key_company')
    )
    op.create_index(op.f('ix_enumerations_company_id'), 'enumerations', ['company_id'], unique=False)
    op.create_index(op.f('ix_enumerations_type'), 'enumerations', ['type'], unique=False)
    op.create_index(op.f('ix_enumerations_key'), 'enumerations', ['key'], unique=False)
    op.create_index('ix_enumerations_type_company_active', 'enumerations', ['type', 'company_id', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_enumerations_type_company_active', table_name='enumerations')
    op.drop_index(op.f('ix_enumerations_key'), table_name='enumerations')
    op.drop_index(op.f('ix_enumerations_type'), table_name='enumerations')
    op.drop_index(op.f('ix_enumerations_company_id'), table_name='enumerations')
    op.drop_table('enumerations')
