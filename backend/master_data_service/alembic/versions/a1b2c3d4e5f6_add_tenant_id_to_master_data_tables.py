# pyre-ignore-all-errors[21]
"""add_tenant_id_to_master_data_tables

Revision ID: a1b2c3d4e5f6
Revises: e5703c10603a
Create Date: 2026-03-25

Adds tenant_id (nullable initially to allow migration on existing data),
plus company_id and group_id if missing, to all MultiTenantBase tables.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cc4ea7bf91a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All tables that inherit from MultiTenantBase in master_data_service
TABLES = [
    "products",
    "product_versions",
    "warehouses",
    "movement_concepts",
    "product_brands",
    "product_categories",
    "uoms",
    "uom_conversions",
    "product_prices",
]

def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :t"
        ),
        {"t": table}
    )
    return result.scalar() > 0

def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column}
    )
    return result.scalar() > 0


def upgrade() -> None:
    for table in TABLES:
        if not _table_exists(table):
            continue
            
        # tenant_id
        if not _column_exists(table, "tenant_id"):
            op.add_column(
                table,
                sa.Column("tenant_id", sa.UUID(as_uuid=True), nullable=True)
            )
            op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"], unique=False)

        # company_id  (may already exist from an earlier baseline)
        if not _column_exists(table, "company_id"):
            op.add_column(
                table,
                sa.Column("company_id", sa.UUID(as_uuid=True), nullable=True)
            )
            op.create_index(f"ix_{table}_company_id", table, ["company_id"], unique=False)

        # group_id
        if not _column_exists(table, "group_id"):
            op.add_column(
                table,
                sa.Column("group_id", sa.UUID(as_uuid=True), nullable=True)
            )
            op.create_index(f"ix_{table}_group_id", table, ["group_id"], unique=False)


def downgrade() -> None:
    for table in reversed(TABLES):
        for col in ["group_id", "tenant_id", "company_id"]:
            if _column_exists(table, col):
                op.drop_index(f"ix_{table}_{col}", table_name=table)
                op.drop_column(table, col)
