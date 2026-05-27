"""add_timezone_to_company

Revision ID: 99a023377b4d
Revises: a1b2c3d4e5f6
Create Date: 2026-05-27 22:04:24.690003

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '99a023377b4d'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('companies', sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'))


def downgrade():
    op.drop_column('companies', 'timezone')