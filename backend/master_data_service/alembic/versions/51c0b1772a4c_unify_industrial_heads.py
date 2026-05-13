"""unify industrial heads

Revision ID: 51c0b1772a4c
Revises: b45c9a28e3a1, 5d92f2693957
Create Date: 2026-05-13 05:02:55.894466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51c0b1772a4c'
down_revision: Union[str, None] = ('b45c9a28e3a1', '5d92f2693957')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
