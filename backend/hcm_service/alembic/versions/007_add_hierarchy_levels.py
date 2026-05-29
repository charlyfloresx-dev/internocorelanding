"""hcm: add authority_level + manager_id + director_id to collaborators (Phase 158)

Migrates 3-level organizational hierarchy from legacy .NET Interno.HumanResource.
authority_level reflects the 7-level catalog (DIRECTOR→MANAGER→SUPERVISOR→
SPECIALIST→TECHNICAL→EMPLOYEE→ASSISTANT).

All hierarchy FKs are soft (no DB constraint) per Iron Wall ADR-02.

Revision ID: 007_add_hierarchy_levels
Revises: 006_add_break_groups
Create Date: 2026-05-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '007_add_hierarchy_levels'
down_revision: Union[str, None] = '006_add_break_groups'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('collaborators',
        sa.Column('authority_level', sa.String(20), nullable=True))
    op.create_index('ix_collaborator_authority_level', 'collaborators', ['authority_level'])

    op.add_column('collaborators',
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_collaborator_manager_id', 'collaborators', ['manager_id'])

    op.add_column('collaborators',
        sa.Column('director_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_collaborator_director_id', 'collaborators', ['director_id'])


def downgrade() -> None:
    op.drop_index('ix_collaborator_director_id', table_name='collaborators')
    op.drop_column('collaborators', 'director_id')
    op.drop_index('ix_collaborator_manager_id', table_name='collaborators')
    op.drop_column('collaborators', 'manager_id')
    op.drop_index('ix_collaborator_authority_level', table_name='collaborators')
    op.drop_column('collaborators', 'authority_level')
