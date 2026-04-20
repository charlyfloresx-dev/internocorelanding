"""add base_currency to company

Revision ID: 4055593d8e6a
Revises: a2f2785f0cb6
Create Date: 2026-03-19 17:07:32.724002

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4055593d8e6a'
down_revision = 'a2f2785f0cb6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Añadir columna como nullable primero
    op.add_column('companies', sa.Column('base_currency', sa.String(length=3), nullable=True))
    
    # 2. Establecer valor por defecto 'USD' para registros existentes
    op.execute("UPDATE companies SET base_currency = 'USD' WHERE base_currency IS NULL")
    
    # 3. Cambiar a NOT NULL
    op.alter_column('companies', 'base_currency', nullable=False)


def downgrade():
    op.drop_column('companies', 'base_currency')