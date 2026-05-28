"""add internal_id_pattern to company

Revision ID: c7d4e5f6a8b9
Revises: 99a023377b4d
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7d4e5f6a8b9'
down_revision = '99a023377b4d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'companies',
        sa.Column('internal_id_pattern', sa.String(200), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('companies', 'internal_id_pattern')
