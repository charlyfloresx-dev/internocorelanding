"""add department description

Revision ID: 003_add_department_description
Revises: a6054c79a22f
Create Date: 2026-05-27

Adds optional description column to departments table.
Mirrors legacy .NET Department.Description (max 250 chars).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_add_department_description'
down_revision: Union[str, None] = 'a6054c79a22f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'departments',
        sa.Column('description', sa.String(length=250), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('departments', 'description')
