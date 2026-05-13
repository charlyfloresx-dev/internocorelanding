"""
Schema Migration Script - Inventory Service
Applies incremental DDL changes that cannot be handled by SQLAlchemy's create_all.
Safe to run multiple times (idempotent) - uses IF NOT EXISTS / DO NOTHING patterns.
"""
import asyncio
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ─── Migration Definitions ───────────────────────────────────────────────────
# Each migration is a tuple: (description, SQL statement)
MIGRATIONS = [
    (
        "Add location column to inventory_movements",
        "ALTER TABLE inventory_movements ADD COLUMN IF NOT EXISTS location VARCHAR(50);"
    ),
    # ── ICT: Create transfer_status_enum ──────────────────────────────────────
    (
        "Create transfer_status_enum type",
        """
        DO $$ BEGIN
            CREATE TYPE transfer_status_enum AS ENUM (
                'PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    ),
    # ── ICT: Create inter_company_transfers table ─────────────────────────────
    (
        "Create inter_company_transfers table",
        """
        CREATE TABLE IF NOT EXISTS inter_company_transfers (
            -- PK & Multitenancy (from MultiTenantBase)
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id              UUID NOT NULL,          -- Empresa A (origin)

            -- Folio & Status
            folio                   VARCHAR(60) UNIQUE NOT NULL,
            status                  transfer_status_enum NOT NULL DEFAULT 'PENDING',

            -- Parties
            destination_company_id  UUID NOT NULL,

            -- Warehouses
            origin_warehouse_id     UUID NOT NULL,
            destination_warehouse_id UUID NOT NULL,
            transit_warehouse_id    UUID NOT NULL,

            -- Product
            product_id              UUID NOT NULL,
            uom_id                  UUID NOT NULL,
            quantity                NUMERIC(18, 4) NOT NULL,
            weight                  NUMERIC(18, 4) NOT NULL DEFAULT 0,
            unit_price_at_dispatch  NUMERIC(18, 4) DEFAULT 0,

            -- SKU Cross-Company Mapping
            origin_sku              VARCHAR(100),
            destination_sku         VARCHAR(100),
            destination_product_id  UUID,

            -- Dispatch metadata (Empresa A)
            shipped_at              TIMESTAMPTZ,
            shipped_by              UUID,

            -- Reception metadata (Empresa B)
            received_at             TIMESTAMPTZ,
            received_by             UUID,
            received_quantity       NUMERIC(18, 4),

            -- Notes and external ref
            notes                   TEXT,
            external_reference      VARCHAR(100),

            -- Forensic traceability: Movement IDs
            dispatch_movement_id    UUID,
            receive_movement_id     UUID,

            -- Audit (from MultiTenantBase)
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by              UUID,
            updated_at              TIMESTAMPTZ,
            version_id              INTEGER DEFAULT 1
        );
        """
    ),
    # ── ICT: Create indexes ───────────────────────────────────────────────────
    (
        "Create ix_ict_company_id index",
        "CREATE INDEX IF NOT EXISTS ix_ict_company_id ON inter_company_transfers (company_id);"
    ),
    (
        "Create ix_ict_destination_company_id index",
        "CREATE INDEX IF NOT EXISTS ix_ict_destination_company_id ON inter_company_transfers (destination_company_id);"
    ),
    (
        "Create ix_ict_status index",
        "CREATE INDEX IF NOT EXISTS ix_ict_status ON inter_company_transfers (status);"
    ),
    (
        "Create ix_ict_product_id index",
        "CREATE INDEX IF NOT EXISTS ix_ict_product_id ON inter_company_transfers (product_id);"
    ),
    # ── ICT: Add financial pricing columns ───────────────────────────────────
    (
        "Add wac_at_dispatch to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS wac_at_dispatch NUMERIC(18, 4);"
    ),
    (
        "Add transfer_revenue_a to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS transfer_revenue_a NUMERIC(18, 4);"
    ),
    (
        "Add acquisition_cost_b to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS acquisition_cost_b NUMERIC(18, 4);"
    ),
    # ── Phase 33.5: Mirror Document Tracking ─────────────────────────────────
    (
        "Add mirror_document_id to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS mirror_document_id UUID;"
    ),
    (
        "Add inbound_folio to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS inbound_folio VARCHAR(60);"
    ),
    (
        "Create index ix_ict_mirror_document_id",
        "CREATE INDEX IF NOT EXISTS ix_ict_mirror_document_id ON inter_company_transfers (mirror_document_id);"
    ),
    # ── Phase 34: Money Value Object Refactor ─────────────────────────────────
    (
        "Add unit_price_amount and currency to inventory_movements",
        "ALTER TABLE inventory_movements ADD COLUMN IF NOT EXISTS unit_price_amount NUMERIC(18, 4) DEFAULT 0, ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'MXN';"
    ),
    (
        "Add unit_price_amount and currency to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS unit_price_amount NUMERIC(18, 4) DEFAULT 0, ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'MXN';"
    ),
    (
        "Add wac_origin_amount to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS wac_origin_amount NUMERIC(18, 4);"
    ),
    (
        "Add revenue_a_amount to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS revenue_a_amount NUMERIC(18, 4);"
    ),
    (
        "Add cost_b_amount to inter_company_transfers",
        "ALTER TABLE inter_company_transfers ADD COLUMN IF NOT EXISTS cost_b_amount NUMERIC(18, 4);"
    ),
    # ── Phase 34.1: InventoryLevel Money VO ───────────────────────────────────
    (
        "Add money columns to inventory_levels",
        """
        ALTER TABLE inventory_levels 
            ADD COLUMN IF NOT EXISTS wac_amount NUMERIC(18, 4) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS wac_currency VARCHAR(3) DEFAULT 'USD',
            ADD COLUMN IF NOT EXISTS last_price_amount NUMERIC(18, 4) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS last_price_currency VARCHAR(3) DEFAULT 'USD',
            ADD COLUMN IF NOT EXISTS replacement_price_amount NUMERIC(18, 4) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS replacement_price_currency VARCHAR(3) DEFAULT 'USD';
        """
    ),
    (
        "Migrate data to new inventory_levels money columns",
        """
        DO $$ 
        BEGIN 
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inventory_levels' AND column_name='weighted_average_cost') THEN
                UPDATE inventory_levels SET wac_amount = weighted_average_cost WHERE wac_amount = 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inventory_levels' AND column_name='last_purchase_price') THEN
                UPDATE inventory_levels SET last_price_amount = last_purchase_price WHERE last_price_amount = 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inventory_levels' AND column_name='replacement_price') THEN
                UPDATE inventory_levels SET replacement_price_amount = replacement_price WHERE replacement_price_amount = 0;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inventory_levels' AND column_name='currency_code') THEN
                UPDATE inventory_levels 
                SET wac_currency = currency_code, 
                    last_price_currency = currency_code, 
                    replacement_price_currency = currency_code 
                WHERE wac_currency = 'USD';
            END IF;
        END $$;
        """
    ),
    # ── Phase 34.2: ICT Enhancements (is_transit & external_ref) ──────────────
    (
        "Add is_transit to inventory_warehouses",
        "ALTER TABLE inventory_warehouses ADD COLUMN IF NOT EXISTS is_transit BOOLEAN DEFAULT FALSE;"
    ),
    (
        "Add external_reference to inventory_documents",
        "ALTER TABLE inventory_documents ADD COLUMN IF NOT EXISTS external_reference VARCHAR(100);"
    ),
    (
        "Add financial columns to inventory_documents",
        "ALTER TABLE inventory_documents ADD COLUMN IF NOT EXISTS total_amount NUMERIC(18, 4) DEFAULT 0, ADD COLUMN IF NOT EXISTS total_currency VARCHAR(3) DEFAULT 'USD';"
    ),
]

# ─── Apply Migrations ─────────────────────────────────────────────────────────
async def apply_migrations(engine):
    """Run all pending migrations. Requires an already-constructed engine.
    Safe to call on startup (idempotent — uses IF NOT EXISTS)."""
    
    # IMPORTANTE: Generar tablas faltantes antes de migrar
    from common.models import Base
    import inventory_app.models.inventory
    import inventory_app.models.inter_company_transfer
    import inventory_app.models.document
    import inventory_app.models.movement
    import inventory_app.models.warehouse
    import inventory_app.models.backflush_error
    import inventory_app.models.bom
    import inventory_app.models.customs_pedimento
    import inventory_app.models.item_variant
    import inventory_app.models.stock
    import inventory_app.models.stock_lot
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[SCHEMA] ✅  Base.metadata.create_all ejecutado exitosamente.")
    except Exception as e:
        logger.error(f"[SCHEMA] ❌ Error en create_all: {e}")

    for description, sql in MIGRATIONS:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql))
            logger.info(f"[MIGRATION] ✅  {description}")
        except Exception as e:
            logger.warning(f"[MIGRATION] ⚠️  Skipped '{description}': {e}")

    logger.info("[MIGRATION] All migrations applied.")


if __name__ == "__main__":
    """Standalone usage: python scripts/migrate_schema.py"""
    from common.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine

    logging.basicConfig(level=logging.INFO)
    db_url = str(settings.DATABASE_URL)
    if not db_url:
        print("ERROR: DATABASE_URL is not configured in settings.")
        raise SystemExit(1)

    standalone_engine = create_async_engine(db_url, pool_pre_ping=True, echo=False)
    asyncio.run(apply_migrations(standalone_engine))
