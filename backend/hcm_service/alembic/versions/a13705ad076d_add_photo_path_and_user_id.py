# Generic single-database configuration.


"""add_photo_path_and_user_id

Revision ID: a13705ad076d
Revises: b2c3d4e5f6a7
Create Date: 2026-05-16 03:55:27.854228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a13705ad076d'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('collaborators', sa.Column('photo_path', sa.String(255), nullable=True))
    op.add_column('collaborators', sa.Column('user_id', sa.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_collaborators_user_id'), 'collaborators', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_collaborators_user_id'), table_name='collaborators')
    op.drop_column('collaborators', 'user_id')
    op.drop_column('collaborators', 'photo_path')
