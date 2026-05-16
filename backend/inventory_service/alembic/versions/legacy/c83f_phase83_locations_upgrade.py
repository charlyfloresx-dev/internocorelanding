"""Phase 83: Industrial Location Model upgrade

Revision ID: c83f_phase83
Revises: a5c404f77598
Create Date: 2026-05-13

Upgrades inventory_locations from basic (warehouse_id, code, max_capacity, zone)
to full Phase 83 spatial model with hierarchical addressing and Density Guard support.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c83f_phase83'
down_revision: Union[str, None] = 'fe63_val_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Hierarchical Addressing ─────────────────────────────────────────
    op.add_column('inventory_locations', sa.Column('aisle', sa.String(10), nullable=True))
    op.add_column('inventory_locations', sa.Column('section', sa.String(10), nullable=True))
    op.add_column('inventory_locations', sa.Column('level', sa.String(10), nullable=True))
    op.add_column('inventory_locations', sa.Column('bin_slot', sa.String(10), nullable=True))

    # ── Operational Classification ──────────────────────────────────────
    op.add_column('inventory_locations', sa.Column('zone_type', sa.String(20), nullable=False, server_default='STORAGE'))
    op.add_column('inventory_locations', sa.Column('storage_type', sa.String(20), nullable=False, server_default='DRY'))
    op.add_column('inventory_locations', sa.Column('is_multisku', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('inventory_locations', sa.Column('velocity_code', sa.String(1), nullable=True))

    # ── Density Guard: Physical Capacity Limits ─────────────────────────
    op.add_column('inventory_locations', sa.Column('max_capacity_units', sa.Numeric(15, 4), nullable=False, server_default='0'))
    op.add_column('inventory_locations', sa.Column('max_weight_kg', sa.Numeric(15, 4), nullable=False, server_default='0'))

    # ── Spatial Dimensions ──────────────────────────────────────────────
    op.add_column('inventory_locations', sa.Column('width_cm', sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('inventory_locations', sa.Column('height_cm', sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('inventory_locations', sa.Column('depth_cm', sa.Numeric(10, 2), nullable=False, server_default='0'))

    # ── Denormalized Occupancy Cache ────────────────────────────────────
    op.add_column('inventory_locations', sa.Column('current_units', sa.Numeric(15, 4), nullable=False, server_default='0'))
    op.add_column('inventory_locations', sa.Column('current_weight_kg', sa.Numeric(15, 4), nullable=False, server_default='0'))

    # ── Virtual Location Flag ───────────────────────────────────────────
    op.add_column('inventory_locations', sa.Column('is_virtual', sa.Boolean(), nullable=False, server_default='false'))

    # ── Drop legacy columns ─────────────────────────────────────────────
    # 'max_capacity' and 'zone' replaced by the new columns above
    try:
        op.drop_column('inventory_locations', 'max_capacity')
    except Exception:
        pass
    try:
        op.drop_column('inventory_locations', 'zone')
    except Exception:
        pass


def downgrade() -> None:
    cols = [
        'is_virtual', 'current_weight_kg', 'current_units',
        'depth_cm', 'height_cm', 'width_cm',
        'max_weight_kg', 'max_capacity_units',
        'velocity_code', 'is_multisku', 'storage_type', 'zone_type',
        'bin_slot', 'level', 'section', 'aisle'
    ]
    for col in cols:
        op.drop_column('inventory_locations', col)
    op.add_column('inventory_locations', sa.Column('max_capacity', sa.Numeric(15, 4), nullable=True))
    op.add_column('inventory_locations', sa.Column('zone', sa.String(50), nullable=True))
