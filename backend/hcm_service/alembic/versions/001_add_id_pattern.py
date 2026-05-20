"""add_id_pattern

Revision ID: 001_add_id_pattern
Revises: 000_hcm_baseline
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_add_id_pattern'
down_revision: Union[str, None] = '000_hcm_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('hr_tenant_configs', sa.Column('internal_id_pattern', sa.String(length=200), nullable=True))
    op.add_column('hr_tenant_configs', sa.Column('pattern_error_message', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('hr_tenant_configs', 'pattern_error_message')
    op.drop_column('hr_tenant_configs', 'internal_id_pattern')
