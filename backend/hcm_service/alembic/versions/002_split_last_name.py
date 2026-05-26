"""split last_name into paternal and maternal

Revision ID: 002_split_last_name
Revises: 73964464b417
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_split_last_name'
down_revision: Union[str, None] = '73964464b417'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns as nullable first to avoid NOT NULL constraint during migration
    op.add_column('collaborators', sa.Column('last_name_paternal', sa.String(length=50), nullable=True))
    op.add_column('collaborators', sa.Column('last_name_maternal', sa.String(length=50), nullable=True))

    # 2. Copy existing last_name data into paternal column
    op.execute("UPDATE collaborators SET last_name_paternal = last_name")

    # 3. Enforce NOT NULL on paternal now that data is populated
    op.alter_column('collaborators', 'last_name_paternal', nullable=False)

    # 4. Drop the old single last_name column
    op.drop_column('collaborators', 'last_name')


def downgrade() -> None:
    op.add_column('collaborators', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.execute(
        "UPDATE collaborators SET last_name = "
        "CONCAT(last_name_paternal, CASE WHEN last_name_maternal IS NOT NULL THEN ' ' || last_name_maternal ELSE '' END)"
    )
    op.alter_column('collaborators', 'last_name', nullable=False)
    op.drop_column('collaborators', 'last_name_maternal')
    op.drop_column('collaborators', 'last_name_paternal')
