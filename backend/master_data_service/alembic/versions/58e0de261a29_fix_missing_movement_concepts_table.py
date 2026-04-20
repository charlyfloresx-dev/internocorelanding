"""fix_missing_movement_concepts_table

Revision ID: 58e0de261a29
Revises: be0c6aad1657
Create Date: 2026-04-04 19:50:57.344337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58e0de261a29'
down_revision: Union[str, None] = 'be0c6aad1657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if the Enum already exists to avoid collisions
    # (Sometimes baseline migrations don't create it explicitly but rely on sa.Enum auto-creation)
    op.create_table('movement_concepts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.Enum('ENTRY', 'OUTPUT', 'TRANSFER', name='movementtype'), nullable=False),
        sa.Column('requires_external_entity', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_target_warehouse', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movement_concepts_code'), 'movement_concepts', ['code'], unique=False)
    op.create_index(op.f('ix_movement_concepts_company_id'), 'movement_concepts', ['company_id'], unique=False)
    op.create_index(op.f('ix_movement_concepts_tenant_id'), 'movement_concepts', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_movement_concepts_tenant_id'), table_name='movement_concepts')
    op.drop_index(op.f('ix_movement_concepts_company_id'), table_name='movement_concepts')
    op.drop_index(op.f('ix_movement_concepts_code'), table_name='movement_concepts')
    op.drop_table('movement_concepts')
