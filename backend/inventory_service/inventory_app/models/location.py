"""
models/location.py
------------------
[Phase 83] Industrial Location Model — Tier-1 WMS Upgrade.
Evolves from a simple String field to a full spatial entity with:
- Hierarchical addressing: Aisle / Section / Level / Bin (PA-SEC-NV-POS)
- Physical limits: max_capacity_units, max_weight_kg, volumetric dimensions
- Denormalized occupancy cache: current_units, current_weight_kg (for O(1) Density Guard)
- Zone & Storage classification for operational routing
- Virtual location support: SYS_RECEIVING, SYS_TRANSIT, SYS_QUALITY

Legacy .NET Audit Note:
  The original Interno.Inventory (.NET) had NO location modeling — only a float
  Capacity field at the Warehouse level. This model is a greenfield advancement.
"""

import uuid
import enum
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase

# ─── ENUMS ────────────────────────────────────────────────────────────────────

class ZoneType(str, enum.Enum):
    RECEIVING  = "RECEIVING"   # Muelle de entrada (SYS_RECEIVING)
    STORAGE    = "STORAGE"     # Almacenamiento estándar en rack
    PICKING    = "PICKING"     # Zona de surtido (alta rotación)
    QUALITY    = "QUALITY"     # Cuarentena / Control de calidad
    SHIPPING   = "SHIPPING"    # Muelle de salida (SYS_SHIPPING)
    TRANSIT    = "TRANSIT"     # Tránsito entre operaciones (SYS_TRANSIT)

class StorageType(str, enum.Enum):
    DRY    = "DRY"     # Almacenamiento seco estándar
    COLD   = "COLD"    # Refrigerado (requiere equipo especial)
    HAZMAT = "HAZMAT"  # Materiales peligrosos
    LOCKED = "LOCKED"  # Bajo llave (alto valor / controlados)


# ─── MODEL ────────────────────────────────────────────────────────────────────

try:
    from master_app.models.location import InventoryLocation
    _REUSED_LOCATION = True
except (ImportError, Exception):
    _REUSED_LOCATION = False

if not _REUSED_LOCATION:
    class InventoryLocation(MultiTenantBase):
        """
        [Phase 83] Industrial Warehouse Location.
        Supports PA-SEC-NV-POS addressing, volumetric Density Guard,
        and denormalized occupancy cache for O(1) capacity validation.
        
        Naming Convention:
            code format: {AISLE}-{SECTION}-{LEVEL}-{BIN}
            example: "01-05-02-A"  → Pasillo 01, Sección 05, Nivel 02, Bin A
        """
        __tablename__ = "inventory_locations"

        # ── Identity ──────────────────────────────────────────────────────────
        warehouse_id: Mapped[uuid.UUID] = mapped_column(
            UUID, index=True, nullable=False
        )
        code: Mapped[str] = mapped_column(
            String(50), index=True, nullable=False,
            comment="Primary scan code. Format: PA-SEC-NV-POS (e.g. 01-05-02-A)"
        )

        # ── Hierarchical Addressing (PA-SEC-NV-POS) ──────────────────────────
        aisle:    Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="Pasillo")
        section:  Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="Columna/Bay")
        level:    Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="Nivel/Shelf")
        bin_slot: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="Gaveta/Bin")

        # ── Operational Classification ────────────────────────────────────────
        zone_type: Mapped[str] = mapped_column(
            String(20), nullable=False, default=ZoneType.STORAGE,
            comment="Functional zone: RECEIVING, STORAGE, PICKING, QUALITY, SHIPPING, TRANSIT"
        )
        storage_type: Mapped[str] = mapped_column(
            String(20), nullable=False, default=StorageType.DRY,
            comment="Environmental requirement: DRY, COLD, HAZMAT, LOCKED"
        )
        is_multisku: Mapped[bool] = mapped_column(
            Boolean, default=True,
            comment="If False, only one SKU is allowed (e.g. medical/regulated items)"
        )
        velocity_code: Mapped[Optional[str]] = mapped_column(
            String(1), nullable=True,
            comment="A=High rotation (near shipping), B=Medium, C=Slow/Dead stock"
        )

        # ── Density Guard: Physical Capacity Limits ───────────────────────────
        max_capacity_units: Mapped[Decimal] = mapped_column(
            Numeric(15, 4), default=Decimal("0.0"),
            comment="Max units (pieces). 0 = unlimited."
        )
        max_weight_kg: Mapped[Decimal] = mapped_column(
            Numeric(15, 4), default=Decimal("0.0"),
            comment="Max weight in kg. 0 = unlimited. SAFETY-CRITICAL: no manager override."
        )

        # ── Spatial Dimensions (cm) for Volumetric Guard ──────────────────────
        width_cm:  Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"))
        height_cm: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"))
        depth_cm:  Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"))

        # ── Denormalized Occupancy Cache (O(1) Density Guard) ─────────────────
        # INVARIANT: Updated atomically via SQL UPDATE + RETURNING on every relocate.
        # NEVER update these from application logic directly — always use
        # repo.increment_location_occupancy() to prevent race conditions.
        current_units: Mapped[Decimal] = mapped_column(
            Numeric(15, 4), default=Decimal("0.0"),
            comment="Current unit count. Denormalized cache — updated atomically."
        )
        current_weight_kg: Mapped[Decimal] = mapped_column(
            Numeric(15, 4), default=Decimal("0.0"),
            comment="Current weight in kg. Denormalized cache — updated atomically."
        )

        # ── Virtual Location Flag ─────────────────────────────────────────────
        is_virtual: Mapped[bool] = mapped_column(
            Boolean, default=False,
            comment="True for system-managed zones: SYS_RECEIVING, SYS_TRANSIT, SYS_QUALITY"
        )

        # ── Table Constraints ─────────────────────────────────────────────────
        __table_args__ = (
            UniqueConstraint(
                "company_id", "warehouse_id", "code",
                name="uq_location_per_warehouse"
            ),
            {"extend_existing": True},
        )

        # ── Computed Properties ───────────────────────────────────────────────
        @property
        def volume_cm3(self) -> Decimal:
            """Total slot volume in cubic centimeters."""
            return self.width_cm * self.height_cm * self.depth_cm

        @property
        def utilization_percent(self) -> float:
            """Percentage of unit capacity currently in use. 0 if unlimited."""
            if not self.max_capacity_units or self.max_capacity_units == 0:
                return 0.0
            return round(float(self.current_units / self.max_capacity_units) * 100, 1)

        @property
        def available_space(self) -> Optional[Decimal]:
            """Remaining unit capacity. None if unlimited."""
            if not self.max_capacity_units or self.max_capacity_units == 0:
                return None
            return max(Decimal("0.0"), self.max_capacity_units - self.current_units)

        @property
        def density_status(self) -> str:
            """Traffic-light status for the UI semaphore."""
            pct = self.utilization_percent
            if pct == 0 and self.max_capacity_units == 0:
                return "UNLIMITED"
            if pct < 70:
                return "OK"
            if pct < 95:
                return "WARNING"
            if pct <= 100:
                return "FULL"
            return "OVERFLOW"

        def __repr__(self):
            return (
                f"<InventoryLocation(code={self.code}, "
                f"zone={self.zone_type}, "
                f"units={self.current_units}/{self.max_capacity_units})>"
            )
