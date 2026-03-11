"""add_readonly_to_subscription

Revision ID: e83f67806528
Revises: 
Create Date: 2026-03-03 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e83f67806528'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Sa.Boolean default is False by default in the model, 
    # but we force server_default for existing rows.
    op.add_column('subscriptions', sa.Column('readonly', sa.Boolean(), nullable=False, server_default='false'))

def downgrade() -> None:
    op.drop_column('subscriptions', 'readonly')
