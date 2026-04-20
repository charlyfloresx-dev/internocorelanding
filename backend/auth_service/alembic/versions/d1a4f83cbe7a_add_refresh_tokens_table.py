"""
Alembic migration: add refresh_tokens table.

Revision: d1a4f83cbe7a
Down revision: 765d720a47b1  (add_trace_id_to_audit_logs)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = "d1a4f83cbe7a"
down_revision = "eb347eb48b7c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # SHA-256 hex digest — never plaintext
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # Audit columns from AuditBase (created_at)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # Composite index for fast lookup (user refreshing a specific company)
    op.create_index("ix_refresh_tokens_user_company", "refresh_tokens", ["user_id", "company_id"])
    # Index for O(1) lookup by token hash during refresh
    op.create_index("ix_refresh_tokens_hash", "refresh_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_company", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
