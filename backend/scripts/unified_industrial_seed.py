"""
InternoCore - Unified Industrial Seed v4
==========================================
Orden de carga:
  1. Auth Core:      BusinessGroup -> Company -> Roles -> User Charly
  2. Master Data:    UOMs -> MovementConcepts -> Warehouse -> Location -> Product -> Prices
  3. Inventory:      Shadow Warehouses -> Product Variants (5 productos x 3 variantes)

Diseno: Savepoints anidados por seccion para idempotencia industrial.
        Cada seccion puede fallar de forma aislada sin revertir las demas.

Fuentes integradas:
  - seed_variants.py         (5 productos, 3 variantes c/u)
  - setup_transfer_prices.py (precios MXN + USD por producto)
"""
import asyncio
import uuid
import logging
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text, and_
from sqlalchemy.exc import IntegrityError

from common.config import settings
from common.models import Company, BusinessGroup
from common.services.audit_service import AuditService
from common.enums import MovementType, ProductType
from auth_app.models.user import User
from auth_app.models.user_credential import UserCredential
from auth_app.models.role import Role
from auth_app.models.user_company_role import UserCompanyRole
from auth_app.core.security import hash_password
from master_app.models.uom import UOM
from master_app.models.movement_concept import MovementConcept
from master_app.models.warehouse import Warehouse as MasterWarehouse
from master_app.models.location import InventoryLocation
from master_app.models.product import Product
from inventory_app.models.warehouse import Warehouse as InvWarehouse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("industrial-seed")

# --- IDs de Continuidad (SSOT) ---
GROUP_ID      = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")
CHARLY_ID     = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
TECH_ONE_ID   = uuid.UUID("11111111-bbaa-46e6-a7f0-aeb4b92b6d38")
TECH_TWO_ID   = uuid.UUID("22222222-bbaa-46e6-a7f0-aeb4b92b6d38")

# Catálogo de Productos y Variantes (SSOT — 5 productos x 3 variantes)
# Fuente: seed_variants.py + setup_transfer_prices.py
PRODUCT_CATALOG = [
    {
        "name": "Engine Control Module (ECM)",
        "sku": "ECM-600",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001"),
        "base_mxn": 495.0,
        "mx_to_us_usd": 29.70,
        "variants": [
            {"brand": "Bosch",          "mpn": "MPN-BOS-601", "price": 450.0, "weight": 1.2},
            {"brand": "Denso",          "mpn": "MPN-DEN-602", "price": 485.0, "weight": 1.1},
            {"brand": "Magneti Marelli","mpn": "MPN-MM-603",  "price": 420.0, "weight": 1.3},
        ]
    },
    {
        "name": "Turbocharger Assembly",
        "sku": "TRB-700",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000002"),
        "base_mxn": 1320.0,
        "mx_to_us_usd": 79.20,
        "variants": [
            {"brand": "Garrett",    "mpn": "MPN-GAR-701", "price": 1200.0, "weight": 5.5},
            {"brand": "BorgWarner", "mpn": "MPN-BOR-702", "price": 1150.0, "weight": 5.8},
            {"brand": "Mitsubishi", "mpn": "MPN-MHI-703", "price": 1100.0, "weight": 5.6},
        ]
    },
    {
        "name": "Brake Disc Rotor",
        "sku": "BRK-800",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000003"),
        "base_mxn": 165.0,
        "mx_to_us_usd": 9.90,
        "variants": [
            {"brand": "Brembo",  "mpn": "MPN-BRE-801", "price": 150.0, "weight": 8.5},
            {"brand": "Akebono", "mpn": "MPN-AKE-802", "price": 135.0, "weight": 8.0},
            {"brand": "Bosch",   "mpn": "MPN-BOS-803", "price": 110.0, "weight": 8.2},
        ]
    },
    {
        "name": "Fuel Injector Set",
        "sku": "FLI-900",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000004"),
        "base_mxn": 352.0,
        "mx_to_us_usd": 21.12,
        "variants": [
            {"brand": "Siemens VDO",  "mpn": "MPN-SIE-901", "price": 320.0, "weight": 0.4},
            {"brand": "Delphi Pro",   "mpn": "MPN-DEL-902", "price": 310.0, "weight": 0.4},
            {"brand": "Hitachi Power", "mpn": "MPN-HIT-903", "price": 295.0, "weight": 0.5},
        ]
    },
    {
        "name": "Suspension Damper",
        "sku": "SUS-100",
        "id": uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000005"),
        "base_mxn": 308.0,
        "mx_to_us_usd": 18.48,
        "variants": [
            {"brand": "Bilstein", "mpn": "MPN-BIL-101", "price": 280.0, "weight": 3.2},
            {"brand": "Ohlins",   "mpn": "MPN-OHL-102", "price": 550.0, "weight": 2.8},
            {"brand": "KYB",      "mpn": "MPN-KYB-103", "price": 145.0, "weight": 3.5},
        ]
    },
]

# --- Helpers ---
async def _first(session, stmt):
    return (await session.execute(stmt)).scalars().first()

async def _safe_add(session, obj, label=""):
    try:
        async with session.begin_nested():
            session.add(obj)
            await session.flush()
            
            # [Fase 84] Auditoria Forense en Seed
            await AuditService.log_action(
                db=session,
                user_id="SYSTEM_SEED",
                action="SEED_CREATE",
                entity_name=obj.__class__.__name__,
                entity_id=getattr(obj, "id", "N/A"),
                company_id=getattr(obj, "company_id", None)
            )
        log.info("  OK   %s", label)
    except IntegrityError as e:
        log.warning("  SKIP %s (already exists: %s)", label, e.orig)
    except Exception as e:
        log.warning("  SKIP %s (failed: %s)", label, type(e).__name__)

# --- Secciones de Seed ---
async def seed_auth(session):
    log.info("[1/5] Auth Core: BusinessGroup / Companies / Roles / Usuarios...")

    if not await session.get(BusinessGroup, GROUP_ID):
        await _safe_add(session, BusinessGroup(
            id=GROUP_ID, name="Interno Global Operations", version_id=1, is_active=True
        ), "BusinessGroup")

    for co_id, co_name in [
        (ENTERPRISE_ID, "Interno Enterprise"),
        (LOGISTICS_MX_ID, "Interno Logistics MX"),
        (LOGISTICS_US_ID, "Interno Logistics US")
    ]:
        if not await session.get(Company, co_id):
            await _safe_add(session, Company(
                id=co_id, name=co_name,
                status="ACTIVE", parent_group_id=GROUP_ID, version_id=1, is_active=True
            ), f"Empresa: {co_name}")

    role_admin = await _first(session, select(Role).where(Role.name == "admin"))
    if not role_admin:
        role_admin = Role(id=uuid.uuid4(), name="admin", is_system_role=True, tenant_id=ENTERPRISE_ID, version_id=1, is_active=True)
        await _safe_add(session, role_admin, "Rol: admin")
        role_admin = await _first(session, select(Role).where(Role.name == "admin"))

    if not await session.get(User, CHARLY_ID):
        charly = User(
            id=CHARLY_ID,
            first_name="Charly",
            last_name_pat="Flores",
            version_id=1,
            is_active=True
        )
        await _safe_add(session, charly, "Usuario (Perfil): Charly Flores")

        # Credenciales de Auth
        charly_cred = UserCredential(
            id=uuid.uuid4(),
            user_id=CHARLY_ID,
            email="charly@interno.com",
            credential_type="PASSWORD",
            hashed_password=hash_password("charly123"),
            version_id=1,
            is_active=True
        )
        await _safe_add(session, charly_cred, "Usuario (Auth): charly@interno.com")

        if role_admin:
            for sys_co_id in [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID]:
                await _safe_add(session, UserCompanyRole(
                    user_id=CHARLY_ID, company_id=sys_co_id,
                    role_id=role_admin.id, tenant_id=sys_co_id,
                    scopes=["*"], is_new=False, version_id=1
                ), f"RBAC: Charly -> admin en {sys_co_id}")

    # Seed Technicians
    role_tech = await _first(session, select(Role).where(Role.name == "technician"))
    if not role_tech:
        role_tech = Role(id=uuid.uuid4(), name="technician", is_system_role=True, tenant_id=ENTERPRISE_ID, version_id=1, is_active=True)
        await _safe_add(session, role_tech, "Rol: technician")
        role_tech = await _first(session, select(Role).where(Role.name == "technician"))

    techs = [
        (TECH_ONE_ID, "Roberto", "Mecánico", "roberto@interno.com"),
        (TECH_TWO_ID, "Ana", "Operadora", "ana@interno.com")
    ]
    
    for tid, fname, lname, email in techs:
        if not await session.get(User, tid):
            user_obj = User(
                id=tid, first_name=fname, last_name_pat=lname, version_id=1, is_active=True
            )
            await _safe_add(session, user_obj, f"Usuario: {fname} {lname}")
            
            cred_obj = UserCredential(
                id=uuid.uuid4(), user_id=tid, email=email, credential_type="PASSWORD",
                hashed_password=hash_password("tech123"), version_id=1, is_active=True
            )
            await _safe_add(session, cred_obj, f"Usuario (Auth): {email}")
            
            if role_tech:
                for sys_co_id in [LOGISTICS_MX_ID, LOGISTICS_US_ID]:
                    await _safe_add(session, UserCompanyRole(
                        user_id=tid, company_id=sys_co_id, role_id=role_tech.id,
                        tenant_id=sys_co_id, scopes=["*"], is_new=False, version_id=1
                    ), f"RBAC: {fname} -> technician en {sys_co_id}")


async def seed_master_data(session):
    log.info("[2/5] Master Data: Catalogos, Almacenes y Ubicaciones...")

    uom_pz = await _first(session, select(UOM).where(UOM.code == "PZ"))
    if not uom_pz:
        uom_pz = UOM(id=uuid.uuid4(), code="PZ", name="Pieces", abbreviation="PZ", company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, version_id=1, is_active=True)
        await _safe_add(session, uom_pz, "UOM: PZ (Pieces)")
        uom_pz = await _first(session, select(UOM).where(UOM.code == "PZ"))

    # Cleanup: Deactivate legacy English concepts to avoid bilingual clutter
    legacy_codes = ["PUR-REC", "SAL-DIS", "INT-TRA"]
    await session.execute(text("""
        UPDATE movement_concepts 
        SET is_active = FALSE 
        WHERE code = ANY(:codes) AND company_id = :co_id
    """), {"codes": legacy_codes, "co_id": ENTERPRISE_ID})

    
    concepts_to_seed = [

        ("Compra", MovementType.ENTRY, "ENT-PUR", True, False),
        ("Ajuste Positivo", MovementType.ENTRY, "ENT-ADJ", False, False),
        ("Venta", MovementType.OUTPUT, "SAL-VEN", True, False),
        ("Ajuste Negativo", MovementType.OUTPUT, "SAL-ADJ", False, False),
        ("Traspaso Interno", MovementType.TRANSFER, "TRF-INT", False, True),
    ]

    for cname, ctype, ccode, req_ext, req_wh in concepts_to_seed:
        c_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.concept.{ENTERPRISE_ID}.{ccode}")
        if not await _first(session, select(MovementConcept).where(MovementConcept.id == c_id)):
            await _safe_add(session, MovementConcept(
                id=c_id, 
                name=cname, 
                code=ccode, 
                type=ctype, 
                requires_external_entity=req_ext,
                requires_target_warehouse=req_wh,
                company_id=ENTERPRISE_ID, 
                tenant_id=ENTERPRISE_ID, 
                group_id=GROUP_ID, 
                version_id=1, 
                is_active=True
            ), f"Concept: {cname}")


    # Warehouses
    wh_ent_id = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.ENT-MAIN")
    wh_ent = await _first(session, select(MasterWarehouse).where(MasterWarehouse.id == wh_ent_id))
    if not wh_ent:
        wh_ent = MasterWarehouse(id=wh_ent_id, name="ALMACEN CENTRAL", code="WH-001", company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, version_id=1, is_active=True)
        await _safe_add(session, wh_ent, "Almacen Master: WH-001")
        wh_ent = await _first(session, select(MasterWarehouse).where(MasterWarehouse.id == wh_ent_id))

    # --- Master Locations ---
    from inventory_app.models.location import InventoryLocation as WmsLocation
    await _safe_add(session, WmsLocation(id=uuid.uuid4(), code="LOC-AUDIT-01", warehouse_id=wh_ent.id, company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, max_capacity_units=100.0, zone_type="QUALITY", storage_type="DRY", version_id=1, is_active=True), "Ubicacion: LOC-AUDIT-01")
    await _safe_add(session, WmsLocation(id=uuid.uuid4(), code="LOC-TIJ-RECV-01", warehouse_id=wh_ent.id, company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, zone_type="RECEIVING", storage_type="DRY", max_capacity_units=500.0, version_id=1, is_active=True), "Ubicacion: LOC-TIJ-RECV-01")

    # Catalog & Prices
    log.info("[3/5] Master Data: 5 Productos, Precios MXN/USD y Variantes...")
    for prod in PRODUCT_CATALOG:
        m_prod = await session.get(Product, prod['id'])
        if not m_prod and uom_pz:
            await _safe_add(session, Product(id=prod['id'], sku=prod['sku'], name=prod['name'], company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, base_uom_id=uom_pz.id, product_type=ProductType.GOODS, version_id=1, is_active=True, min_order_qty=1.0, max_order_qty=1000.0, safety_stock=5.0), f"Producto: {prod['sku']}")

        # Transfer Price MXN (Enterprise -> Logistics)
        await session.execute(text("""
            INSERT INTO product_prices (
                id, product_id, price_list_index, amount, currency, 
                unit_type, is_active, is_manual, version_id, company_id, tenant_id
            ) VALUES (
                :id, :prod_id, 4, :amount, 'MXN', 
                'SALE', TRUE, FALSE, 1, :co_id, :co_id
            ) ON CONFLICT DO NOTHING;
        """), {"id": uuid.uuid4(), "prod_id": prod['id'], "amount": Decimal(str(prod['base_mxn'])), "co_id": ENTERPRISE_ID})

        # Transfer Price USD (Logistics MX -> Logistics US)
        await session.execute(text("""
            INSERT INTO product_prices (
                id, product_id, price_list_index, amount, currency, 
                unit_type, is_active, is_manual, version_id, company_id, tenant_id
            ) VALUES (
                :id, :prod_id, 4, :amount, 'USD', 
                'SALE', TRUE, FALSE, 1, :co_id, :co_id
            ) ON CONFLICT DO NOTHING;
        """), {"id": uuid.uuid4(), "prod_id": prod['id'], "amount": Decimal(str(prod['mx_to_us_usd'])), "co_id": LOGISTICS_MX_ID})


async def seed_inventory(session):
    log.info("[4/5] Inventory Context: Shadow Warehouses y Variantes...")
    
    # Sincronizar Warehouses al schema de inventario
    for wh_id, name, code, cy, cntry in [
        (uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.ENT-MAIN"), "Almacen Central", "WH-001", ENTERPRISE_ID, "MX"),
        (uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-MX-TJ"), "Logistics MX TJ", "LOG-MX-TJ", LOGISTICS_MX_ID, "MX"),
        (uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-US-SD"), "Logistics US SD", "LOG-US-SD", LOGISTICS_US_ID, "US"),
    ]:
        await session.execute(text("""
            INSERT INTO inventory_warehouses (
                id, name, company_id, tenant_id, code, type, is_active, version_id, is_transit, created_at, country_code
            ) VALUES (
                :id, :name, :co, :co, :code, 'PHYSICAL', TRUE, 1, FALSE, NOW(), :cntry
            ) ON CONFLICT DO NOTHING;
        """), {"id": wh_id, "name": name, "co": cy, "code": code, "cntry": cntry})
        log.info(f"  OK   Shadow WH: {code}")

    now = datetime.now(timezone.utc)
    for prod in PRODUCT_CATALOG:
        for var in prod['variants']:
            await session.execute(text("""
                INSERT INTO inventory_item_variants (
                    id, product_id, internal_sku, brand, mfg_part_number, 
                    unit_price, weight, is_preferred, is_active, version_id,
                    company_id, tenant_id, created_at
                ) VALUES (
                    :id, :prod_id, :sku, :brand, :mpn, 
                    :price, :weight, FALSE, TRUE, 1,
                    :co_id, :co_id, :now
                ) ON CONFLICT DO NOTHING;
            """), {
                "id": uuid.uuid4(), "prod_id": prod['id'], "sku": prod['sku'],
                "brand": var['brand'], "mpn": var['mpn'],
                "price": Decimal(str(var['price'])), "weight": Decimal(str(var['weight'])),
                "co_id": ENTERPRISE_ID, "now": now
            })
            log.info(f"  OK   Variante: {var['mpn']}")


# --- Orquestador Principal ---
async def run_unified_seed():
    log.info("=" * 55)
    log.info("   InternoCore - Unified Industrial Seed v4")
    log.info("=" * 55)
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        log.info("[1/5] Auth Core: BusinessGroup / Companies / Roles / Usuarios...")
        await seed_auth(session)

        log.info("[2/5] Master Data: Catalogos, Almacenes y Ubicaciones...")
        await seed_master_data(session)

        log.info("[4/5] Inventory Context: Shadow Warehouses y Variantes...")
        await seed_inventory(session)
        
        await session.commit()
        log.info("[+] Secciones 1-4 comprometidas exitosamente.")
        
    # [Phase 83] Run the industrial locations layout and initial stock flows
    try:
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(backend_dir)
        sys.path.append(os.path.join(backend_dir, "inventory_service"))
        sys.path.append(os.path.join(backend_dir, "inventory_service", "scripts"))
        
        from flows.seed_locations import seed_locations
        log.info("[5/5] WMS Industrial Layout: Generando Racks y Posiciones...")
        await seed_locations()
        
        from flows.flow_1_entry import run_flow_1
        log.info("[+] Seeding Initial Stock (Flow 1)...")
        await run_flow_1()
    except Exception as e:
        log.warning(f"Failed to run external seed flows: {e}")

    log.info("=" * 55)
    log.info("   SEED COMPLETED SUCCESSFULLY")
    log.info("=" * 55)

if __name__ == "__main__":
    asyncio.run(run_unified_seed())
