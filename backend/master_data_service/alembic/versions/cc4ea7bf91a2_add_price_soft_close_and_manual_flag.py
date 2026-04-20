"""add_price_soft_close_and_manual_flag

Revision ID: cc4ea7bf91a2
Revises: bb3da9fcddfd
Create Date: 2026-03-21 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc4ea7bf91a2'
down_revision: Union[str, None] = 'e5703c10603a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add valid_until for Soft-Close / Price History Timeline.
    # NULL = precio vigente. Con timestamp = precio histórico cerrado.
    op.add_column('product_prices',
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True)
    )

    # Add is_manual audit flag.
    # False = precio oficial de un tabulador (listas 1-10).
    # True = precio sobrescrito manualmente por el operador en una transacción.
    op.add_column('product_prices',
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )

    # Index for efficient querying of current (active) prices: WHERE valid_until IS NULL
    op.create_index('ix_product_prices_valid_until', 'product_prices', ['valid_until'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_product_prices_valid_until', table_name='product_prices')
    op.drop_column('product_prices', 'is_manual')
    op.drop_column('product_prices', 'valid_until')
