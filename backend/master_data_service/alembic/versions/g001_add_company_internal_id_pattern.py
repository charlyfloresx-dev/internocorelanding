"""master_data: add internal_id_pattern to companies

Column added to common.models.company.Company in Phase 118 (HCM) but
the master_data_service migration was missing, causing the seed script
to fail with UndefinedColumnError on every container startup.

Revision ID: g001_company_id_pattern
Revises: f21020a05ace
Create Date: 2026-05-30
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'g001_company_id_pattern'
down_revision: Union[str, None] = 'b5c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'companies',
        sa.Column('internal_id_pattern', sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('companies', 'internal_id_pattern')
