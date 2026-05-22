"""Make reference_code unique per company

Revision ID: 002_ref_code_composite
Revises: 001_add_assigned_department_id
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_ref_code_composite'
down_revision: Union[str, None] = '001_add_assigned_department_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _constraint_exists(table, constraint_name):
    from sqlalchemy import inspect as sa_inspect
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    constraints = [c['name'] for c in inspector.get_unique_constraints(table)]
    return constraint_name in constraints

def upgrade() -> None:
    # Drop global unique constraint on reference_code
    if _constraint_exists('tickets', 'tickets_reference_code_key'):
        op.drop_constraint('tickets_reference_code_key', 'tickets', type_='unique')
    
    # Create composite unique constraint on (company_id, reference_code)
    if not _constraint_exists('tickets', 'tickets_company_id_reference_code_key'):
        op.create_unique_constraint('tickets_company_id_reference_code_key', 'tickets', ['company_id', 'reference_code'])

def downgrade() -> None:
    # Drop composite unique constraint
    if _constraint_exists('tickets', 'tickets_company_id_reference_code_key'):
        op.drop_constraint('tickets_company_id_reference_code_key', 'tickets', type_='unique')
    
    # Re-create global unique constraint on reference_code
    if not _constraint_exists('tickets', 'tickets_reference_code_key'):
        op.create_unique_constraint('tickets_reference_code_key', 'tickets', ['reference_code'])
