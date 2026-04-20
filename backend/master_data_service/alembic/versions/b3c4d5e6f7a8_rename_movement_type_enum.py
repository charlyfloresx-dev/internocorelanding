"""rename_movement_type_enum

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-25

Renames the movementtype enum labels from Spanish to English to match the Python model.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def type_exists(type_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM pg_type WHERE typname = :t"),
        {"t": type_name}
    )
    return result.scalar() > 0

def upgrade() -> None:
    if not type_exists("movementtype"):
        return
    # Postgres 15 allows renaming enum labels
    op.execute("ALTER TYPE movementtype RENAME VALUE 'ENTRADA' TO 'ENTRY'")
    op.execute("ALTER TYPE movementtype RENAME VALUE 'SALIDA' TO 'OUTPUT'")
    op.execute("ALTER TYPE movementtype RENAME VALUE 'TRASPASO' TO 'TRANSFER'")

def downgrade() -> None:
    op.execute("ALTER TYPE movementtype RENAME VALUE 'ENTRY' TO 'ENTRADA'")
    op.execute("ALTER TYPE movementtype RENAME VALUE 'OUTPUT' TO 'SALIDA'")
    op.execute("ALTER TYPE movementtype RENAME VALUE 'TRANSFER' TO 'TRASPASO'")
