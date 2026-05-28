"""mes: add alias and release_date to work orders

Revision ID: 007_add_workorder_alias_release_date
Revises: 006_mes_cycle_time_and_breaks
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa

revision = '007_wo_alias'
down_revision = '006_mes_cycle_time_and_breaks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('mes_work_orders', sa.Column('alias', sa.String(100), nullable=True))
    op.add_column('mes_work_orders', sa.Column('release_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('mes_work_orders', 'release_date')
    op.drop_column('mes_work_orders', 'alias')
