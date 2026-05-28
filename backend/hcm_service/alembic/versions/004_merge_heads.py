"""hcm: merge divergent heads (split_last_name + department_description)

Revision ID: 004_merge_heads
Revises: 002_split_last_name, 003_add_department_description
Create Date: 2026-05-27

"""
from typing import Sequence, Union
from alembic import op

revision: str = '004_merge_heads'
down_revision: Union[str, Sequence[str]] = ('002_split_last_name', '003_add_department_description')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
