"""Add Customs and FIFO fields

Revision ID: dc2611da6e2c
Revises: 86a6ad039d59
Create Date: 2026-04-01 08:55:50.406132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc2611da6e2c'
down_revision: Union[str, None] = '86a6ad039d59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create customs_pedimentos table
    op.create_table(
        'customs_pedimentos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('pedimento_number', sa.String(length=15), nullable=False),
        sa.Column('customs_key', sa.String(length=10), nullable=False),
        sa.Column('operation_type', sa.Enum('IMPORT', 'EXPORT', name='customsoperationtype'), nullable=False),
        sa.Column('customs_date', sa.DateTime(), nullable=False),
        sa.Column('is_temporary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('exchange_rate_dof', sa.Float(), nullable=True),
        sa.Column('comments', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pedimento_number')
    )
    op.create_index(op.f('ix_customs_pedimentos_company_id'), 'customs_pedimentos', ['company_id'], unique=False)
    op.create_index(op.f('ix_customs_pedimentos_tenant_id'), 'customs_pedimentos', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_customs_pedimentos_group_id'), 'customs_pedimentos', ['group_id'], unique=False)
    op.create_index(op.f('ix_customs_pedimentos_customs_date'), 'customs_pedimentos', ['customs_date'], unique=False)
    op.create_index(op.f('ix_customs_pedimentos_pedimento_number'), 'customs_pedimentos', ['pedimento_number'], unique=True)

    # 2. Update inventory_movements table
    op.add_column('inventory_movements', sa.Column('available_quantity', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))
    op.add_column('inventory_movements', sa.Column('customs_pedimento_id', sa.UUID(), nullable=True))
    op.add_column('inventory_movements', sa.Column('source_movement_id', sa.UUID(), nullable=True))
    op.add_column('inventory_movements', sa.Column('expiry_date', sa.DateTime(), nullable=True))
    
    op.create_index(op.f('ix_inventory_movements_customs_pedimento_id'), 'inventory_movements', ['customs_pedimento_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_source_movement_id'), 'inventory_movements', ['source_movement_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_movements_source_movement_id'), table_name='inventory_movements')
    op.drop_index(op.f('ix_inventory_movements_customs_pedimento_id'), table_name='inventory_movements')
    op.drop_column('inventory_movements', 'expiry_date')
    op.drop_column('inventory_movements', 'source_movement_id')
    op.drop_column('inventory_movements', 'customs_pedimento_id')
    op.drop_column('inventory_movements', 'available_quantity')
    
    op.drop_table('customs_pedimentos')
    sa.Enum(name='customsoperationtype').drop(op.get_bind(), checkfirst=False)
