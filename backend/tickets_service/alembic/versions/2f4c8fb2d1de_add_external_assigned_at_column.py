"""add_external_assigned_at_column

Revision ID: 2f4c8fb2d1de
Revises: c8e7d9b2a1f0
Create Date: 2026-05-08 17:26:32.385354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f4c8fb2d1de'
down_revision: Union[str, None] = 'c8e7d9b2a1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('tickets')]
    
    if 'external_assigned_at' not in existing_cols:
        op.add_column('tickets', sa.Column('external_assigned_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tickets', 'external_assigned_at')
