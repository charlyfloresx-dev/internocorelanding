"""add_timezone_to_company

Revision ID: a6b1698e23e1
Revises: 002_add_inventory_item_variants
Create Date: 2026-05-27 22:04:33.550611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a6b1698e23e1'
down_revision: Union[str, None] = '002_add_inventory_item_variants'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'))


def downgrade() -> None:
    op.drop_column('companies', 'timezone')
