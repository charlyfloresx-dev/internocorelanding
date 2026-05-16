"""Add default_tax_rate to companies (Cleaned)

Revision ID: 90a121e69a2e
Revises: d53275884ee8
Create Date: 2026-05-12 23:40:05.773607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90a121e69a2e'
down_revision = 'd53275884ee8'
branch_labels = None
depends_on = None


def upgrade():
    # This migration was cleaned up because it contained redundant tables 
    # (enumerations, security_audit_logs) and misplaced tables (inventory_locations).
    # All shared tables are now in init.py or their respective services.
    pass


def downgrade():
    pass