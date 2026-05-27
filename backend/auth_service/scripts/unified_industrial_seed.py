# Content from backend/scripts/unified_industrial_seed.py (Fixed version)
import uuid
import logging
import os
import sys
import asyncio

# 1. Configurar PYTHONPATH para incluir TODAS las carpetas de servicios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Si se corre desde backend/auth_service/scripts, el root esta dos niveles arriba
if "auth_service" in BASE_DIR:
    ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
else:
    ROOT_DIR = os.path.dirname(BASE_DIR)
services = [
    "auth_service", 
    "master_data_service", 
    "inventory_service", 
    "notification_service",
    "tickets_service",
    "mes_service",
    "subscription_service",
    "hcm_service"
]
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
for s in services:
    path = os.path.join(ROOT_DIR, s)
    if path not in sys.path:
        sys.path.append(path)

from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, text, and_
from sqlalchemy.exc import IntegrityError

from common.infrastructure.database import AsyncSessionLocal, engine
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
from common.models.enumeration import Enumeration
from master_app.models.product import Product
from master_app.models.partner import Partner
from inventory_app.models.warehouse import Warehouse as InvWarehouse
from tickets_app.models.ticket import Ticket
from tickets_app.core.constants import TicketStatus, TicketPriority, TicketType
from hcm_app.models.collaborator import Collaborator
from common.models.external_contact import ExternalContact
from subscription_app.models.subscription import Plan, Subscription, Entitlement
from subscription_app.core.enums import ModuleCode, SubscriptionStatus

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
DEMO_ID       = uuid.UUID("d3d3d3d3-bbaa-46e6-a7f0-aeb4b92b6d38")

# Catálogo de Productos y Variantes (SSOT — 5 productos x 3 variantes)
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
            await session.merge(obj)
            await session.flush()
            
            await AuditService.log_action(
                db=session,
                user_id="SYSTEM_SEED",
                action="SEED_UPSERT",
                entity_name=obj.__class__.__name__,
                entity_id=getattr(obj, "id", "N/A"),
                company_id=getattr(obj, "company_id", None)
            )
        log.info("  DONE %s (Merged)", label)
    except Exception as e:
        log.warning("  FAIL %s (error: %s)", label, type(e).__name__)

async def seed_enumerations(session):
    log.info("[0/5] Global Enumerations...")
    enums_to_seed = [
        {"type": "TICKET_STATUS", "key": "OPEN", "label": "Abierto", "t_key": "enums.ticket_status.open", "sort": 1},
        {"type": "TICKET_STATUS", "key": "IN_PROGRESS", "label": "En Progreso", "t_key": "enums.ticket_status.in_progress", "sort": 2},
        {"type": "TICKET_STATUS", "key": "RESOLVED", "label": "Resuelto", "t_key": "enums.ticket_status.resolved", "sort": 3},
        {"type": "TICKET_STATUS", "key": "CLOSED", "label": "Cerrado", "t_key": "enums.ticket_status.closed", "sort": 4},
        {"type": "TICKET_PRIORITY", "key": "LOW", "label": "Baja", "t_key": "enums.ticket_priority.low", "sort": 1},
        {"type": "TICKET_PRIORITY", "key": "MEDIUM", "label": "Media", "t_key": "enums.ticket_priority.medium", "sort": 2},
        {"type": "TICKET_PRIORITY", "key": "HIGH", "label": "Alta", "t_key": "enums.ticket_priority.high", "sort": 3},
        {"type": "TICKET_PRIORITY", "key": "CRITICAL", "label": "Crítica", "t_key": "enums.ticket_priority.critical", "sort": 4},
        {"type": "INVENTORY_MOVEMENT_TYPE", "key": "ENTRADA", "label": "Entrada", "t_key": "inventory.movement.entrada", "sort": 1},
        {"type": "INVENTORY_MOVEMENT_TYPE", "key": "SALIDA", "label": "Salida", "t_key": "inventory.movement.salida", "sort": 2},
        {"type": "INVENTORY_MOVEMENT_TYPE", "key": "TRASPASO", "label": "Traspaso", "t_key": "inventory.movement.traspaso", "sort": 3},
        {"type": "PRODUCT_STATUS", "key": "ACTIVE", "label": "Activo", "t_key": "enums.product_status.active", "sort": 2},
        {"type": "PRODUCT_TYPE", "key": "GOODS", "label": "Material / Producto", "t_key": "enums.product_type.goods", "sort": 1},
        {"type": "CURRENCY", "key": "MXN", "label": "Pesos Mexicanos", "t_key": "enums.currency.mxn", "sort": 1},
        {"type": "CURRENCY", "key": "USD", "label": "Dólares Americanos", "t_key": "enums.currency.usd", "sort": 2},
    ]
    for e in enums_to_seed:
        stmt = select(Enumeration).where(Enumeration.type == e["type"], Enumeration.key == e["key"], Enumeration.company_id == None)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if not existing:
            await _safe_add(session, Enumeration(
                id=uuid.uuid4(), type=e["type"], key=e["key"], label=e["label"],
                translation_key=e["t_key"], sort_order=e["sort"],
                company_id=None, tenant_id=None, is_active=True, version_id=1, created_by=CHARLY_ID
            ), f"Enum: {e['type']}.{e['key']}")

async def seed_auth(session):
    log.info("[1/5] Auth Core...")
    if not await session.get(BusinessGroup, GROUP_ID):
        await _safe_add(session, BusinessGroup(id=GROUP_ID, name="Interno Global Operations", version_id=1, is_active=True), "BusinessGroup")

    company_data = [
        (ENTERPRISE_ID, "Interno Enterprise", 0.16, "America/Monterrey"),
        (LOGISTICS_MX_ID, "Planta MX", 0.16, "America/Monterrey"),
        (LOGISTICS_US_ID, "Planta US", 0.0, "America/Chicago"),
        (DEMO_ID, "Demo Operativo S.A.", 0.16, "America/Monterrey"),
    ]
    for co_id, co_name, co_tax, co_tz in company_data:
        company = await session.get(Company, co_id)
        if not company:
            await _safe_add(session, Company(
                id=co_id, name=co_name, status="ACTIVE", parent_group_id=GROUP_ID,
                version_id=1, is_active=True, default_tax_rate=co_tax, timezone=co_tz
            ), f"Empresa: {co_name}")
        else:
            company.timezone = co_tz
            company.default_tax_rate = co_tax

    role_admin = await _first(session, select(Role).where(Role.name == "admin"))
    if not role_admin:
        role_admin = Role(id=uuid.uuid4(), name="admin", is_system_role=True, tenant_id=ENTERPRISE_ID, version_id=1, is_active=True)
        await _safe_add(session, role_admin, "Rol: admin")
        role_admin = await _first(session, select(Role).where(Role.name == "admin"))

    if not await session.get(User, CHARLY_ID):
        charly = User(id=CHARLY_ID, first_name="Charly", last_name_pat="Flores", version_id=1, is_active=True)
        await _safe_add(session, charly, "Usuario: Charly")
        charly_cred = UserCredential(id=uuid.uuid4(), user_id=CHARLY_ID, email="charly@interno.com", credential_type="PASSWORD", hashed_password=hash_password("charly123"), version_id=1, is_active=True)
        await _safe_add(session, charly_cred, "Auth: charly@interno.com")
        if role_admin:
            for sys_co_id in [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID, DEMO_ID]:
                await _safe_add(session, UserCompanyRole(user_id=CHARLY_ID, company_id=sys_co_id, role_id=role_admin.id, tenant_id=sys_co_id, scopes=["*"], is_new=False, version_id=1), f"RBAC Charly -> {sys_co_id}")

async def seed_subscriptions(session):
    log.info("[1.5/5] Subscriptions...")
    enterprise_plan = Plan(id=uuid.UUID("11111111-1111-4111-b111-000000000001"), name="Industrial Enterprise", modules=["AUTH_CORE", "INVENTORY_CORE", "MASTER_DATA_CORE", "HCM_CORE", "WMS_CORE", "MES_CORE", "TICKETS_CORE"])
    await _safe_add(session, enterprise_plan, "Plan: Enterprise")
    for cid in [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID, DEMO_ID]:
        sub = Subscription(id=uuid.uuid5(uuid.NAMESPACE_DNS, f"sub-{cid}"), company_id=cid, tenant_id=cid, plan_id=enterprise_plan.id, status=SubscriptionStatus.ACTIVE, start_date=datetime.now(timezone.utc))
        await _safe_add(session, sub, f"Sub: {cid}")
        for mod in enterprise_plan.modules:
            await _safe_add(session, Entitlement(id=uuid.uuid5(uuid.NAMESPACE_DNS, f"ent-{cid}-{mod}"), company_id=cid, tenant_id=cid, module_code=mod, is_enabled=True, source_subscription_id=sub.id), f"Ent: {mod}")

async def seed_master_data(session):
    log.info("[2/5] Master Data...")
    uom_pz = await _first(session, select(UOM).where(UOM.code == "PZ"))
    if not uom_pz:
        await _safe_add(session, UOM(id=uuid.uuid4(), code="PZ", name="Pieces", abbreviation="PZ", company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, version_id=1, is_active=True), "UOM: PZ")
    
    concepts = [("Compra", MovementType.ENTRY, "ENT-PUR", "inventory.concept.purchase"), ("Venta", MovementType.OUTPUT, "SAL-VEN", "inventory.concept.sale")]
    for name, ctype, code, tkey in concepts:
        cid = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.concept.{ENTERPRISE_ID}.{code}")
        if not await session.get(MovementConcept, cid):
            await _safe_add(session, MovementConcept(id=cid, name=name, code=code, type=ctype, translation_key=tkey, company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, version_id=1, is_active=True), f"Concept: {code}")

async def seed_industrial_identities(session):
    log.info("[5/5] Industrial Identities (Collaborators)...")
    from hcm_app.core.security import hash_rfid, hash_pin
    CARLOS_ID = uuid.UUID("11111111-0001-4001-a001-000000000001")
    await _safe_add(session, Collaborator(
        id=CARLOS_ID, internal_id="003709A", first_name="Carlos", last_name="Ramírez", department="Warehouse", 
        rfid_tag=hash_rfid("960091919"), pin_code=hash_pin("1234"), company_id=ENTERPRISE_ID, tenant_id=ENTERPRISE_ID, group_id=GROUP_ID, is_active=True, version_id=1
    ), "Collab: Carlos (003709A)")

# Orchestration
SERVICE_DB_MAP = {"auth": "dbname", "master": "master_data_db", "subscription": "subscription_db", "hcm": "hcm_db", "inventory": "inventory_db", "tickets": "tickets_db"}

def get_session_factory(db_name: str):
    base_url = settings.ASYNC_DATABASE_URL
    import re
    new_url = re.sub(r'/[a-zA-Z0-9_\-]+(\?.*)?$', f'/{db_name}\\1', base_url)
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    engine = create_async_engine(new_url, pool_pre_ping=True)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def run():
    for db_key, db_name in SERVICE_DB_MAP.items():
        factory = get_session_factory(db_name)
        async with factory() as session:
            if db_key == "auth":
                await seed_enumerations(session)
                await seed_auth(session)
            elif db_key == "subscription":
                await seed_subscriptions(session)
            elif db_key == "master":
                await seed_master_data(session)
            elif db_key == "hcm":
                await seed_industrial_identities(session)
            await session.commit()
    log.info("SEED COMPLETED")

if __name__ == "__main__":
    asyncio.run(run())
