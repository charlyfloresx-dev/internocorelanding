"""mes: cycle_time_seconds in standard_times + break_minutes in shifts

Revision ID: 006_mes_cycle_time_and_breaks
Revises: 5e91a2b3c4d5
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '006_mes_cycle_time_and_breaks'
down_revision: Union[str, None] = '5e91a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # cycle_time_seconds: machine cycle time per piece in seconds (legacy: OperationTime.RunTime).
    # NULL = not yet time-studied; ManufacturingMath falls back to set_time_hours.
    op.add_column(
        'mes_standard_times',
        sa.Column('cycle_time_seconds', sa.Integer(), nullable=True)
    )

    # break_minutes: total scheduled break time per shift (lunch + rest breaks).
    # Default 60 matches legacy Interno.HumanResource TotalTimeBreaks hardcoded value.
    op.add_column(
        'mes_shifts',
        sa.Column('break_minutes', sa.Integer(), nullable=False, server_default='60')
    )


def downgrade() -> None:
    op.drop_column('mes_shifts', 'break_minutes')
    op.drop_column('mes_standard_times', 'cycle_time_seconds')
