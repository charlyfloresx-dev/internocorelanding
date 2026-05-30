"""mes: add sequence_number to mes_standard_times

Adds an integer column that defines the execution order of operations
within a manufacturing route per item (e.g. CORTE=10, SOLDADURA=20,
ENSAMBLE=30, INSPECCIÓN=40).

Existing rows are assigned sequence numbers in alphabetical order of
operation_name, incrementing by 10 per position per item+company.

Revision ID: 011_add_standard_time_sequence_number
Revises: 010_fix_shift_code_unique
Create Date: 2026-05-30
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = '011_st_sequence_number'
down_revision: Union[str, None] = '010_fix_shift_code_unique'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add as nullable so existing rows don't violate NOT NULL
    op.add_column(
        'mes_standard_times',
        sa.Column('sequence_number', sa.Integer(), nullable=True),
    )

    # Step 2: Assign ordered values to existing rows (10, 20, 30…) based on
    # alphabetical operation_name within each company+item partition.
    op.execute("""
        UPDATE mes_standard_times st
        SET sequence_number = sub.rn * 10
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY company_id, item_code
                       ORDER BY operation_name
                   ) AS rn
            FROM mes_standard_times
        ) sub
        WHERE st.id = sub.id
    """)

    # Step 3: Make NOT NULL with a server default for future inserts
    op.alter_column(
        'mes_standard_times',
        'sequence_number',
        nullable=False,
        server_default='10',
    )


def downgrade() -> None:
    op.drop_column('mes_standard_times', 'sequence_number')
