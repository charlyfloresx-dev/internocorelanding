"""add versioning to items

Revision ID: wms_versioning_002
Revises: wms_init_001
Create Date: 2026-02-12 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'wms_versioning_002'
down_revision = 'wms_init_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('items', sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'))
    op.drop_constraint('_wms_company_sku_uc', 'items', type_='unique')
    op.create_unique_constraint('_wms_company_sku_version_uc', 'items', ['sku', 'version_number', 'company_id'])


def downgrade() -> None:
    op.drop_constraint('_wms_company_sku_version_uc', 'items', type_='unique')
    op.create_unique_constraint('_wms_company_sku_uc', 'items', ['sku', 'company_id'])
    op.drop_column('items', 'version_number')