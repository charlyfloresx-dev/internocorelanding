"""mes: fix mes_shifts.code unique constraint to be per-company

The original migration (006) created a global unique constraint on 'code',
preventing two companies from having shifts with the same code (e.g. "MAT").
This migration replaces it with a composite unique constraint (company_id, code).

Revision ID: 010_fix_shift_code_unique
Revises: 009_facility_area_resource
Create Date: 2026-05-28
"""
from typing import Sequence, Union
from alembic import op

revision: str = '010_fix_shift_code_unique'
down_revision: Union[str, None] = '009_facility_area_resource'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_mes_shifts_code', table_name='mes_shifts')
    op.drop_constraint('uq_mes_shifts_code', 'mes_shifts', type_='unique')
    op.create_unique_constraint('uq_mes_shifts_company_code', 'mes_shifts', ['company_id', 'code'])


def downgrade() -> None:
    op.drop_constraint('uq_mes_shifts_company_code', 'mes_shifts', type_='unique')
    op.create_unique_constraint('uq_mes_shifts_code', 'mes_shifts', ['code'])
    op.create_index('ix_mes_shifts_code', 'mes_shifts', ['code'], unique=True)
