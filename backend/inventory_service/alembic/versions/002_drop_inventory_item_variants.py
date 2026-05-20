"""drop inventory_item_variants — table moved to master_data_db

Revision ID: 002_drop_inventory_item_variants
Revises: 001_create_audit_logs
Create Date: 2026-05-20

"""
from typing import Sequence, Union
from alembic import op

revision: str = '002_drop_inventory_item_variants'
down_revision: Union[str, None] = '001_create_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    from sqlalchemy import inspect as sa_inspect
    return name in sa_inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _table_exists('inventory_item_variants'):
        op.drop_table('inventory_item_variants')


def downgrade() -> None:
    pass
