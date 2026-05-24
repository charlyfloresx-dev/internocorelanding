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
import os
import sys

# 1. Configurar PYTHONPATH para incluir TODAS las carpetas de servicios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Si se corre desde backend/scripts, el root es un nivel arriba
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
OPERATOR_ID      = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc")
SUPERVISOR_ID    = uuid.UUID("85236974-5678-4cd2-ccbb-987654321def")

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
            await session.merge(obj)
            await session.flush()
            
            # [Fase 84] Auditoria Forense en Seed
            # Must use its own savepoint so a missing audit_logs table
            # does not abort the parent savepoint that holds the real data.
            try:
                async with session.begin_nested():
                    await AuditService.log_action(
                        db=session,
                        user_id="SYSTEM_SEED",
                        action="SEED_UPSERT",
                        entity_name=obj.__class__.__name__,
                        entity_id=getattr(obj, "id", "N/A"),
                        company_id=getattr(obj, "company_id", None)
                    )
            except Exception:
                # Databases like hcm_db / subscription_db lack the audit_logs table.
                # The inner savepoint rolls back cleanly; the outer merge survives.
                pass
                
        log.info("  DONE %s (Merged)", label)
    except Exception as e:
        log.warning("  FAIL %s (error: %s)", label, type(e).__name__)

async def seed_enumerations(session):
    log.info("[0/5] Global Enumerations: Statuses, Priorities and Categories...")
    enums_to_seed = [
        # Tickets & Support
        {"type": "TICKET_STATUS", "key": "OPEN", "label": "Abierto", "t_key": "enums.ticket_status.open", "sort": 1},
        {"type": "TICKET_STATUS", "key": "IN_PROGRESS", "label": "En Progreso", "t_key": "enums.ticket_status.in_progress", "sort": 2},
        {"type": "TICKET_STATUS", "key": "RESOLVED", "label": "Resuelto", "t_key": "enums.ticket_status.resolved", "sort": 3},
        {"type": "TICKET_STATUS", "key": "CLOSED", "label": "Cerrado", "t_key": "enums.ticket_status.closed", "sort": 4},
        {"type": "TICKET_PRIORITY", "key": "LOW", "label": "Baja", "t_key": "enums.ticket_priority.low", "sort": 1},
        {"type": "TICKET_PRIORITY", "key": "MEDIUM", "label": "Media", "t_key": "enums.ticket_priority.medium", "sort": 2},
        {"type": "TICKET_PRIORITY", "key": "HIGH", "label": "Alta", "t_key": "enums.ticket_priority.high", "sort": 3},
        {"type": "TICKET_PRIORITY", "key": "CRITICAL", "label": "Crítica", "t_key": "enums.ticket_priority.critical", "sort": 4},
        
        # Assets & CMMS
        {"type": "ASSET_STATUS", "key": "OPERATIONAL", "label": "Operativo", "t_key": "enums.asset_status.operational", "sort": 1},
        {"type": "ASSET_STATUS", "key": "UNDER_MAINTENANCE", "label": "En Mantenimiento", "t_key": "enums.asset_status.maintenance", "sort": 2},
        {"type": "ASSET_STATUS", "key": "OUT_OF_SERVICE", "label": "Fuera de Servicio", "t_key": "enums.asset_status.out_of_service", "sort": 3},
        {"type": "WORK_ORDER_STATUS", "key": "DRAFT", "label": "Borrador", "t_key": "enums.wo_status.draft", "sort": 1},
        {"type": "WORK_ORDER_STATUS", "key": "SCHEDULED", "label": "Programada", "t_key": "enums.wo_status.scheduled", "sort": 2},
        {"type": "WORK_ORDER_STATUS", "key": "IN_PROGRESS", "label": "En Ejecución", "t_key": "enums.wo_status.in_progress", "sort": 3},
        {"type": "WORK_ORDER_STATUS", "key": "COMPLETED", "label": "Completada", "t_key": "enums.wo_status.completed", "sort": 4},

        # Inventory Movements
        {"type": "INVENTORY_MOVEMENT_TYPE", "key": "ENTRADA", "label": "Entrada", "t_key": "inventory.movement.entrada", "sort": 1},
        {"type": "INVENTORY_MOVEMENT_TYPE", "key": "SALIDA", "label": "Salida", "t_key": "inventory.movement.salida", "sort": 2},
        {"type": "INVENTORY_MOVEMENT_TYPE", "key": "TRASPASO", "label": "Traspaso", "t_key": "inventory.movement.traspaso", "sort": 3},
        
        # Product & Catalog Enums
        {"type": "PRODUCT_STATUS", "key": "DRAFT", "label": "Borrador", "t_key": "enums.product_status.draft", "sort": 1},
        {"type": "PRODUCT_STATUS", "key": "ACTIVE", "label": "Activo", "t_key": "enums.product_status.active", "sort": 2},
        {"type": "PRODUCT_STATUS", "key": "INACTIVE", "label": "Inactivo", "t_key": "enums.product_status.inactive", "sort": 3},
        {"type": "PRODUCT_TYPE", "key": "GOODS", "label": "Material / Producto", "t_key": "enums.product_type.goods", "sort": 1},
        {"type": "PRODUCT_TYPE", "key": "SERVICE", "label": "Servicio", "t_key": "enums.product_type.service", "sort": 2},
        
        # Currency & Finance
        {"type": "CURRENCY", "key": "MXN", "label": "Pesos Mexicanos", "t_key": "enums.currency.mxn", "sort": 1},
        {"type": "CURRENCY", "key": "USD", "label": "Dólares Americanos", "t_key": "enums.currency.usd", "sort": 2},
        
        # Partner Types
        {"type": "PARTNER_TYPE", "key": "CUSTOMER", "label": "Cliente", "t_key": "enums.partner_type.customer", "sort": 1},
        {"type": "PARTNER_TYPE", "key": "SUPPLIER", "label": "Proveedor", "t_key": "enums.partner_type.supplier", "sort": 2},
        
        # Warehouse Types
        {"type": "WAREHOUSE_TYPE", "key": "PHYSICAL", "label": "Almacén Físico", "t_key": "enums.wh_type.physical", "sort": 1},
        {"type": "WAREHOUSE_TYPE", "key": "VIRTUAL", "label": "Almacén Virtual", "t_key": "enums.wh_type.virtual", "sort": 2},
        {"type": "WAREHOUSE_TYPE", "key": "TRANSIT", "label": "Tránsito", "t_key": "enums.wh_type.transit", "sort": 3},
        {"type": "WAREHOUSE_TYPE", "key": "EXT_PARTNER", "label": "Gestionado por Terceros", "t_key": "enums.wh_type.ext", "sort": 4},
        
        # Inventory Document & Transfer Statuses
        {"type": "DOCUMENT_STATUS", "key": "DRAFT", "label": "Borrador", "t_key": "enums.doc_status.draft", "sort": 1},
        {"type": "DOCUMENT_STATUS", "key": "PROCESSED", "label": "Procesado", "t_key": "enums.doc_status.processed", "sort": 2},
        {"type": "DOCUMENT_STATUS", "key": "CANCELLED", "label": "Cancelado", "t_key": "enums.doc_status.cancelled", "sort": 3},
        {"type": "TRANSFER_STATUS", "key": "PENDING", "label": "Pendiente", "t_key": "enums.trf_status.pending", "sort": 1},
        {"type": "TRANSFER_STATUS", "key": "SHIPPED", "label": "Enviado", "t_key": "enums.trf_status.shipped", "sort": 2},
        {"type": "TRANSFER_STATUS", "key": "DELIVERED", "label": "Recibido", "t_key": "enums.trf_status.delivered", "sort": 3},
        {"type": "TRANSFER_STATUS", "key": "CANCELLED", "label": "Cancelado", "t_key": "enums.trf_status.cancelled", "sort": 4},
        
        # Product Version & Unit Types
        {"type": "VERSION_STATUS", "key": "DESIGN", "label": "Diseño / Especificación", "t_key": "enums.ver_status.design", "sort": 1},
        {"type": "VERSION_STATUS", "key": "EXPERIMENTAL", "label": "Prototipo / Experimental", "t_key": "enums.ver_status.experimental", "sort": 2},
        {"type": "VERSION_STATUS", "key": "PUBLISHED", "label": "Publicado / Vigente", "t_key": "enums.ver_status.published", "sort": 3},
        {"type": "UNIT_TYPE", "key": "BASE", "label": "Unidad Base (Contenedor)", "t_key": "enums.unit_type.base", "sort": 1},
        {"type": "UNIT_TYPE", "key": "SALE", "label": "Unidad de Venta (Pieza)", "t_key": "enums.unit_type.sale", "sort": 2},

        # Payment Methods (global defaults — companies can extend with company_id)
        {"type": "PAYMENT_METHOD", "key": "CASH", "label": "Efectivo", "t_key": "enums.payment_method.cash", "sort": 1},
        {"type": "PAYMENT_METHOD", "key": "CARD", "label": "Tarjeta", "t_key": "enums.payment_method.card", "sort": 2},
        {"type": "PAYMENT_METHOD", "key": "TRANSFER", "label": "Transferencia Bancaria", "t_key": "enums.payment_method.transfer", "sort": 3},
        {"type": "PAYMENT_METHOD", "key": "STRIPE", "label": "Stripe / Pago Online", "t_key": "enums.payment_method.stripe", "sort": 4},
        {"type": "PAYMENT_METHOD", "key": "CREDIT", "label": "Crédito / Cuenta Corriente", "t_key": "enums.payment_method.credit", "sort": 5},
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

# --- Secciones de Seed ---
async def seed_auth(session):
    log.info("[1/5] Auth Core: BusinessGroup / Companies / Roles / Usuarios...")

    if not await session.get(BusinessGroup, GROUP_ID):
        await _safe_add(session, BusinessGroup(
            id=GROUP_ID, name="Interno Global Operations", version_id=1, is_active=True
        ), "BusinessGroup")

    for co_id, co_name, co_tax in [
        (ENTERPRISE_ID, "Interno Enterprise", 0.16),
        (LOGISTICS_MX_ID, "Planta MX", 0.16),
        (LOGISTICS_US_ID, "Planta US", 0.0),
        (DEMO_ID, "Demo Operativo S.A.", 0.16)
    ]:
        if not await session.get(Company, co_id):
            await _safe_add(session, Company(
                id=co_id, name=co_name,
                status="ACTIVE", parent_group_id=GROUP_ID, version_id=1, is_active=True,
                default_tax_rate=co_tax
            ), f"Empresa: {co_name} (IVA: {co_tax*100}%)")

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

        # Credenciales SSO (Google)
        charly_google_cred = UserCredential(
            id=uuid.uuid4(),
            user_id=CHARLY_ID,
            email="charly.flores.x@gmail.com",
            credential_type="GOOGLE",
            version_id=1,
            is_active=True
        )
        await _safe_add(session, charly_google_cred, "Usuario SSO (Auth): charly.flores.x@gmail.com")

        if role_admin:
            for sys_co_id in [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID]:
                await _safe_add(session, UserCompanyRole(
                    user_id=CHARLY_ID, company_id=sys_co_id,
                    role_id=role_admin.id, tenant_id=sys_co_id,
                    scopes=["*"], is_new=False, version_id=1
                ), f"RBAC: Charly -> admin en {sys_co_id}")
            
            # Assignment for Demo Tenant (Operative Scopes)
            await _safe_add(session, UserCompanyRole(
                user_id=CHARLY_ID, company_id=DEMO_ID,
                role_id=role_admin.id, tenant_id=DEMO_ID,
                scopes=["master:catalog:manage", "inv:movements:manage", "tickets:manage", "tickets:view"], 
                is_new=True, version_id=1
            ), f"RBAC: Charly -> Operative Admin en DEMO")

    # Seed Technicians and Additional Users
    role_tech = await _first(session, select(Role).where(Role.name == "technician"))
    if not role_tech:
        role_tech = Role(id=uuid.uuid4(), name="technician", is_system_role=True, tenant_id=ENTERPRISE_ID, version_id=1, is_active=True)
        await _safe_add(session, role_tech, "Rol: technician")
        role_tech = await _first(session, select(Role).where(Role.name == "technician"))

    role_operator = await _first(session, select(Role).where(Role.name == "operator"))
    if not role_operator:
        role_operator = Role(id=uuid.uuid4(), name="operator", is_system_role=True, tenant_id=ENTERPRISE_ID, version_id=1, is_active=True)
        await _safe_add(session, role_operator, "Rol: operator")
        role_operator = await _first(session, select(Role).where(Role.name == "operator"))

    role_manager = await _first(session, select(Role).where(Role.name == "manager"))
    if not role_manager:
        role_manager = Role(id=uuid.uuid4(), name="manager", is_system_role=True, tenant_id=ENTERPRISE_ID, version_id=1, is_active=True)
        await _safe_add(session, role_manager, "Rol: manager")
        role_manager = await _first(session, select(Role).where(Role.name == "manager"))

    techs = [
        (TECH_ONE_ID, "Roberto", "Mecánico", "roberto@interno.com", role_tech, ["*"], [LOGISTICS_MX_ID, LOGISTICS_US_ID], "PASSWORD"),
        (TECH_TWO_ID, "Ana", "Operadora", "ana@interno.com", role_tech, ["*"], [LOGISTICS_MX_ID, LOGISTICS_US_ID], "PASSWORD"),
        (OPERATOR_ID, "Operador", "Demo", "operador@interno.com", role_operator, ["inv:movements:manage"], [LOGISTICS_MX_ID], "PASSWORD"),
        (SUPERVISOR_ID, "Supervisor", "US", "supervisor_us@interno.com", role_manager, ["inv:movements:manage", "inv:warehouse:manage", "master:catalog:manage", "wms:manage", "investments:manage"], [LOGISTICS_US_ID], "PASSWORD")
    ]
    
    for tid, fname, lname, email, trole, tscopes, tcompanies, tcred in techs:
        if not await session.get(User, tid):
            user_obj = User(
                id=tid, first_name=fname, last_name_pat=lname, version_id=1, is_active=True
            )
            await _safe_add(session, user_obj, f"Usuario: {fname} {lname}")
            
            cred_obj = UserCredential(
                id=uuid.uuid4(), user_id=tid, email=email, credential_type=tcred,
                hashed_password=hash_password("ops123") if tcred == "PASSWORD" and tid == OPERATOR_ID else (hash_password("super123") if tcred == "PASSWORD" and tid == SUPERVISOR_ID else (hash_password("tech123") if tcred == "PASSWORD" else None)), version_id=1, is_active=True
            )
            await _safe_add(session, cred_obj, f"Usuario (Auth): {email}")
            
            if trole:
                for sys_co_id in tcompanies:
                    await _safe_add(session, UserCompanyRole(
                        user_id=tid, company_id=sys_co_id, role_id=trole.id,
                        tenant_id=sys_co_id, scopes=tscopes, is_new=False, version_id=1
                    ), f"RBAC: {fname} -> {trole.name} en {sys_co_id}")


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
        ("Compra", MovementType.ENTRY, "ENT-PUR", True, False, "inventory.concept.purchase"),
        ("Ajuste Positivo", MovementType.ENTRY, "ENT-ADJ", False, False, "inventory.concept.adj_pos"),
        ("Venta", MovementType.OUTPUT, "SAL-VEN", True, False, "inventory.concept.sale"),
        ("Ajuste Negativo", MovementType.OUTPUT, "SAL-ADJ", False, False, "inventory.concept.adj_neg"),
        ("Traspaso Interno", MovementType.TRANSFER, "TRF-INT", False, True, "inventory.concept.transfer"),
    ]

    for cname, ctype, ccode, req_ext, req_wh, t_key in concepts_to_seed:
        c_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.concept.{ENTERPRISE_ID}.{ccode}")
        existing_c = await session.get(MovementConcept, c_id)
        if not existing_c:
            await _safe_add(session, MovementConcept(
                id=c_id, 
                name=cname, 
                code=ccode, 
                type=ctype, 
                requires_external_entity=req_ext,
                requires_target_warehouse=req_wh,
                translation_key=t_key,
                company_id=ENTERPRISE_ID, 
                tenant_id=ENTERPRISE_ID, 
                group_id=GROUP_ID, 
                version_id=1, 
                is_active=True
            ), f"Concept: {cname} (NEW)")
        else:
            # Update existing
            existing_c.translation_key = t_key
            existing_c.requires_external_entity = req_ext
            existing_c.requires_target_warehouse = req_wh
            log.info("  UPDATE Concept: %s", cname)


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

    # [Phase 84] Setup Transfer Prices (Enterprise -> Logistics MX -> US)
    try:
        log.info("[3.5/5] Pricing Context: Configurando Precios de Transferencia...")
        # Redirect DATABASE_URL for the sub-script
        master_url = settings.ASYNC_DATABASE_URL.replace("/dbname", "/master_data_db")
        env = os.environ.copy()
        env["DATABASE_URL"] = master_url
        env["PYTHONIOENCODING"] = "utf-8"
        paths_to_add = [
            ROOT_DIR,
            os.path.join(ROOT_DIR, "inventory_service")
        ]
        env["PYTHONPATH"] = os.pathsep.join(paths_to_add) + os.pathsep + env.get("PYTHONPATH", "")
        
        import subprocess
        script_path = os.path.join(ROOT_DIR, "inventory_service", "scripts", "flows", "setup_transfer_prices.py")
        result = subprocess.run(
            [sys.executable, script_path],
            env=env, capture_output=True, text=True
        )
        if result.returncode != 0:
            log.warning(f"Sub-seed failed: {result.stderr}")
        else:
            log.info("   ✅ Precios de transferencia OK.")
    except Exception as e:
        log.warning(f"Failed to run transfer prices seed: {e}")

async def seed_variants_master(session):
    """Seed inventory_item_variants in master_data_db (SSOT since Phase 119)."""
    log.info("[3.6/5] Variants Context: Generando Variantes de Producto en master_data_db...")
    now = datetime.now(timezone.utc)
    for prod in PRODUCT_CATALOG:
        for var in prod["variants"]:
            await session.execute(text("""
                INSERT INTO inventory_item_variants (
                    id, product_id, internal_sku, brand, mfg_part_number,
                    unit_price, weight, is_preferred, is_active, version_id,
                    company_id, tenant_id, created_at
                ) VALUES (
                    :id, :prod_id, :sku, :brand, :mpn,
                    :price, :weight, FALSE, TRUE, 1,
                    :co_id, :co_id, :now
                ) ON CONFLICT (company_id, internal_sku, mfg_part_number) DO NOTHING;
            """), {
                "id": uuid.uuid4(), "prod_id": prod["id"], "sku": prod["sku"],
                "brand": var["brand"], "mpn": var["mpn"],
                "price": Decimal(str(var["price"])), "weight": Decimal(str(var["weight"])),
                "co_id": ENTERPRISE_ID, "now": now
            })
    log.info("   ✅ 15 Variantes de producto OK (master_data_db).")


async def seed_inventory(session):
    log.info("[4/5] Inventory Context: Shadow Warehouses y Locaciones...")

    WH_ENT_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.ENT-MAIN")
    WH_MX_ID  = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-MX-TJ")
    WH_US_ID  = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-US-SD")

    # ── 4.1 Shadow Warehouses ─────────────────────────────────────────────────
    for wh_id, name, code, cy, cntry in [
        (WH_ENT_ID, "Almacen Central", "WH-001", ENTERPRISE_ID, "MX"),
        (WH_MX_ID, "Planta MX", "LOG-MX-TJ", LOGISTICS_MX_ID, "MX"),
        (WH_US_ID, "Planta US", "LOG-US-SD", LOGISTICS_US_ID, "US"),
    ]:
        await session.execute(text("""
            INSERT INTO inventory_warehouses (
                id, name, company_id, tenant_id, code, type, is_active, version_id, is_transit, created_at, country_code
            ) VALUES (
                :id, :name, :co, :co, :code, 'PHYSICAL', TRUE, 1, FALSE, NOW(), :cntry
            ) ON CONFLICT DO NOTHING;
        """), {"id": wh_id, "name": name, "co": cy, "code": code, "cntry": cntry})
        log.info(f"  OK   Shadow WH: {code}")

    # ── 4.2 Shadow Movement Concepts (mirror from master_data_db) ─────────────
    log.info("[4.6/5] Movement Concepts Shadow...")
    concepts_data = [
        ("Compra",           "ENTRY",    "ENT-PUR"),
        ("Ajuste Positivo",  "ENTRY",    "ENT-ADJ"),
        ("Venta",            "OUTPUT",   "SAL-VEN"),
        ("Ajuste Negativo",  "OUTPUT",   "SAL-ADJ"),
        ("Traspaso Interno", "TRANSFER", "TRF-INT"),
    ]
    for cname, ctype, ccode in concepts_data:
        c_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.concept.{ENTERPRISE_ID}.{ccode}")
        await session.execute(text("""
            INSERT INTO inventory_movement_concepts (
                id, name, code, type, company_id, tenant_id, group_id,
                version_id, is_active, created_at
            ) VALUES (
                :id, :name, :code, :type, :co, :co, :grp,
                1, TRUE, NOW()
            ) ON CONFLICT DO NOTHING;
        """), {"id": c_id, "name": cname, "code": ccode, "type": ctype,
               "co": ENTERPRISE_ID, "grp": GROUP_ID})
    log.info("   ✅ Movement concepts shadow OK.")

    # ── 4.4 WMS Industrial Locations (Phase 83) ──────────────────────────────
    log.info("[4.7/5] WMS Locations: Zonas virtuales + Rack + Picking...")
    # Locations definition: (code, aisle, section, level, bin, zone, storage, virtual, multisku, max_units, max_kg, velocity, w, h, d)
    locations = [
        # Virtual System Zones
        ("SYS_RECEIVING", "00","00","00","R", "RECEIVING","DRY", True,  True,  9999,  99999, None, 0,0,0),
        ("SYS_TRANSIT",   "00","00","00","T", "TRANSIT",  "DRY", True,  True,  9999,  99999, None, 0,0,0),
        ("SYS_QUALITY",   "00","00","00","Q", "QUALITY",  "DRY", True,  False, 500,   2000,  None, 0,0,0),
        # LOC-AUDIT-01 (used by flows as base location)
        ("LOC-AUDIT-01",  "00","00","00","A", "QUALITY",  "DRY", False, True,  100,   500,   None, 120,100,80),
        # LOC-TIJ-RECV-01
        ("LOC-TIJ-RECV-01","00","00","00","B","RECEIVING","DRY", False, True,  500,   5000,  None, 200,150,100),
    ]
    # Aisle 01 — STORAGE: 3 sections x 4 levels x 2 bins = 24 rack slots
    for sec in range(1, 4):
        for lvl in range(1, 5):
            for b in ["A", "B"]:
                code = f"01-{sec:02d}-{lvl:02d}-{b}"
                locations.append((code, "01", f"{sec:02d}", f"{lvl:02d}", b,
                                  "STORAGE", "DRY", False, True, 150, 400, "B", 120, 100, 80))
    # Aisle 02 — PICKING: 6 positions (velocity A)
    for pos in range(1, 7):
        code = f"02-{pos:02d}-01-A"
        locations.append((code, "02", f"{pos:02d}", "01", "A",
                          "PICKING", "DRY", False, True, 50, 100, "A", 60, 50, 40))

    created_locs = 0
    for loc_data in locations:
        code, aisle, sec, lvl, bn, zone, storage, virtual, multi, mu, mk, vel, w, h, d = loc_data
        await session.execute(text("""
            INSERT INTO inventory_locations (
                id, company_id, tenant_id, warehouse_id, code,
                aisle, section, level, bin_slot,
                zone_type, storage_type, is_virtual, is_multisku,
                max_capacity_units, max_weight_kg,
                width_cm, height_cm, depth_cm,
                current_units, current_weight_kg,
                velocity_code, version_id, is_active, created_at
            ) VALUES (
                :id, :co, :co, :wh, :code,
                :aisle, :sec, :lvl, :bn,
                :zone, :storage, :virt, :multi,
                :mu, :mk,
                :w, :h, :d,
                0, 0,
                :vel, 1, TRUE, NOW()
            ) ON CONFLICT (company_id, warehouse_id, code) DO NOTHING;
        """), {
            "id": uuid.uuid4(), "co": ENTERPRISE_ID, "wh": WH_ENT_ID,
            "code": code, "aisle": aisle, "sec": sec, "lvl": lvl, "bn": bn,
            "zone": zone, "storage": storage, "virt": virtual, "multi": multi,
            "mu": Decimal(str(mu)), "mk": Decimal(str(mk)),
            "w": Decimal(str(w)), "h": Decimal(str(h)), "d": Decimal(str(d)),
            "vel": vel
        })
        created_locs += 1
    log.info(f"   ✅ {created_locs} Locaciones WMS OK (3 virtuales + LOC-AUDIT-01 + 24 rack + 6 picking).")


async def seed_partners(session):
    log.info("[+] Seeding Business Partners...")
    partners = []
    # Seed CUST-0000 (Público General) for all primary companies/tenants
    for cid, label in [
        (ENTERPRISE_ID, "Enterprise"),
        (LOGISTICS_MX_ID, "Planta MX"),
        (LOGISTICS_US_ID, "Planta US"),
        (DEMO_ID, "Demo Tenant")
    ]:
        partners.append(Partner(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, f"partner.default.{cid}"),
            code="CUST-0000",
            name="Público General",
            type="CUSTOMER",
            company_id=cid,
            tenant_id=cid,
            is_active=True
        ))

    # Add other stable partners
    partners.extend([
        Partner(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.general"),
            code="GEN-001",
            name="Público en General",
            type="CUSTOMER",
            company_id=ENTERPRISE_ID,
            tenant_id=ENTERPRISE_ID,
            is_active=True
        ),
        Partner(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.1"),
            code="SUP-IND-01",
            name="Aceros de México S.A.",
            type="SUPPLIER",
            company_id=ENTERPRISE_ID,
            tenant_id=ENTERPRISE_ID,
            is_active=True
        ),
        Partner(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.2"),
            code="CUS-DEMO-01",
            name="Cliente Especial Alpha",
            type="CUSTOMER",
            company_id=ENTERPRISE_ID,
            tenant_id=ENTERPRISE_ID,
            is_active=True
        ),
        Partner(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.3"),
            code="CUS-DEMO-02",
            name="Cliente Especial Beta",
            type="CUSTOMER",
            company_id=ENTERPRISE_ID,
            tenant_id=ENTERPRISE_ID,
            is_active=True
        )
    ])
    for p in partners:
        await _safe_add(session, p, f"Partner: {p.code} - {p.name}")

async def seed_tickets(session):
    log.info("[+] Seeding Support Tickets...")
    tickets = []
    # 5 Tickets for IT
    for i in range(1, 6):
        tickets.append(Ticket(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, f"ticket.it.{i}"),
            reference_code=f"IT-2026-{str(i).zfill(3)}",
            title=f"Mantenimiento de Servidor {i}",
            description=f"Revisión rutinaria de logs y actualizaciones de seguridad en el servidor de aplicación {i}.",
            ticket_type=TicketType.MAINTENANCE,
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.NEW,
            area="Sistemas (IT)",
            company_id=ENTERPRISE_ID,
            tenant_id=ENTERPRISE_ID,
            is_active=True,
            version_id=1
        ))
        
    # 1 Ticket assigned to Charly directly
    tickets.append(Ticket(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, "ticket.sec.001"),
        reference_code="SEC-2026-001",
        title="Auditoría de Roles y Permisos (Urgente)",
        description="Revisar que los accesos al entorno de producción de NexoSuite estén restringidos solo al personal autorizado.",
        ticket_type=TicketType.SUPPORT,
        priority=TicketPriority.CRITICAL,
        status=TicketStatus.IN_PROGRESS,
        area="Seguridad de la Información",
        assigned_to_id=CHARLY_ID,
        company_id=ENTERPRISE_ID,
        tenant_id=ENTERPRISE_ID,
        is_active=True,
        version_id=1
    ))

    # [Phase 89] Ticket for External Provider (Alicia Torres)
    # Token: industrial_demo_token_alicia_2026
    tickets.append(Ticket(
        id=uuid.UUID("33333333-0003-4003-b003-000000000003"),
        reference_code="EXT-2026-001",
        title="Instalación de Sensor de Proximidad RACK-01",
        description="Se requiere instalación y calibración del sensor de proximidad en el rack de auditoría.",
        ticket_type=TicketType.MAINTENANCE,
        priority=TicketPriority.HIGH,
        status=TicketStatus.ASSIGNED,
        area="Mantenimiento Externo",
        external_contact_id=uuid.UUID("22222222-0002-4002-b002-000000000002"),
        external_token="industrial_demo_token_alicia_2026",
        company_id=ENTERPRISE_ID,
        tenant_id=ENTERPRISE_ID,
        is_active=True,
        version_id=1
    ))
    
    for t in tickets:
        await _safe_add(session, t, f"Ticket: {t.reference_code}")

async def seed_industrial_identities(session):
    log.info("[+] Seeding Triple Identity contacts (Collaborators & External)...")
    from hcm_app.core.security import hash_rfid, hash_pin
    
    # ── Carlos Ramírez (Enterprise/Logistics, Supervisor) ──
    CARLOS_ID = uuid.UUID("11111111-0001-4001-a001-000000000001")
    collab_carlos = Collaborator(
        id=CARLOS_ID,
        internal_id="003709A",
        first_name="Carlos",
        last_name="Ramírez",
        is_direct=True,
        supervisor_id=None,
        home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{ENTERPRISE_ID}.WH-TIJ"),
        rfid_tag=hash_rfid("960091919"),
        pin_code=hash_pin("1234"),
        company_id=ENTERPRISE_ID,
        tenant_id=ENTERPRISE_ID,
        group_id=GROUP_ID,
        user_id=CHARLY_ID,
        is_active=True,
        version_id=1
    )
    await _safe_add(session, collab_carlos, "Collaborator: Carlos Ramírez (Enterprise)")

    CARLOS_US_ID = uuid.UUID("11111111-0001-4001-c001-000000000001")
    collab_carlos_us = Collaborator(
        id=CARLOS_US_ID,
        internal_id="003709A",
        first_name="Carlos",
        last_name="Ramírez",
        is_direct=True,
        supervisor_id=None,
        home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_US_ID}.WH-SDY"),
        rfid_tag=hash_rfid("960091919"),
        pin_code=hash_pin("1234"),
        company_id=LOGISTICS_US_ID,
        tenant_id=LOGISTICS_US_ID,
        group_id=GROUP_ID,
        user_id=CHARLY_ID,
        is_active=True,
        version_id=1
    )
    await _safe_add(session, collab_carlos_us, "Collaborator: Carlos Ramírez (Logistics US)")

    # ── Luis Torres (Logistics US/MX, Supervisor) ──
    LUIS_US_ID = uuid.UUID("11111111-0002-4001-c001-000000000002")
    collab_luis_us = Collaborator(
        id=LUIS_US_ID,
        internal_id="801",
        first_name="Luis (USA)",
        last_name="Torres",
        is_direct=True,
        supervisor_id=None,
        home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_US_ID}.WH-SDY"),
        rfid_tag=hash_rfid("2327559684"),
        pin_code=None,
        company_id=LOGISTICS_US_ID,
        tenant_id=LOGISTICS_US_ID,
        group_id=GROUP_ID,
        is_active=True,
        version_id=1
    )
    await _safe_add(session, collab_luis_us, "Collaborator: Luis Torres (Logistics US)")

    # ── Ana García (Logistics MX, Subordinada de Luis) ──
    ANA_ID = uuid.UUID("11111111-0003-4001-a001-000000000003")
    collab_ana = Collaborator(
        id=ANA_ID,
        internal_id="301",
        first_name="Ana",
        last_name="García",
        is_direct=True,
        supervisor_id=LUIS_US_ID, # Just for testing hierarchy
        home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_MX_ID}.WH-TIJ"),
        rfid_tag=None,
        pin_code=hash_pin("1234"),
        company_id=LOGISTICS_MX_ID,
        tenant_id=LOGISTICS_MX_ID,
        group_id=GROUP_ID,
        is_active=True,
        version_id=1
    )
    await _safe_add(session, collab_ana, "Collaborator: Ana García (Logistics MX)")

    # 2. External Contact (Provider)
    contact_data = {
        "full_name": "Ing. Alicia Torres",
        "email": "charly.flores.x@gmail.com",
        "phone": "+52 55 1234 5678",
        "company_id": ENTERPRISE_ID,
        "tenant_id": ENTERPRISE_ID,
        "is_active": True,
        "version_id": 1
    }
    
    # Try to find existing
    stmt = select(ExternalContact).where(ExternalContact.id == uuid.UUID("22222222-0002-4002-b002-000000000002"))
    existing = (await session.execute(stmt)).scalar_one_or_none()
    
    if existing:
        for k, v in contact_data.items():
            setattr(existing, k, v)
        print(f"  UPDATE External Contact: {existing.full_name}")
    else:
        contact = ExternalContact(id=uuid.UUID("22222222-0002-4002-b002-000000000002"), **contact_data)
        session.add(contact)
        print(f"  CREATE External Contact: {contact.full_name}")

async def seed_subscriptions(session):
    log.info("[1.5/5] Subscriptions: Plans, Subscriptions and Entitlements...")
    
    # 1. Seed Plans
    enterprise_plan = Plan(
        id=uuid.UUID("11111111-1111-4111-b111-000000000001"),
        name="Industrial Enterprise",
        description="Full access to all InternoCore modules",
        price=999.0,
        currency="USD",
        modules=["AUTH_CORE", "INVENTORY_CORE", "MASTER_DATA_CORE", "HCM_CORE", "WMS_CORE", "MES_CORE", "TICKETS_CORE"]
    )
    await _safe_add(session, enterprise_plan, "Plan: Industrial Enterprise")

    # 2. Seed Subscriptions & Entitlements for key companies
    companies_to_seed = [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID, DEMO_ID]
    
    for cid in companies_to_seed:
        sub = Subscription(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, f"sub-{cid}"),
            company_id=cid,
            tenant_id=cid,
            plan_id=enterprise_plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.now(timezone.utc),
            status_updated_at=datetime.now(timezone.utc)
        )
        await _safe_add(session, sub, f"Subscription for {cid}")

        # Seed Entitlements (Truth Table)
        for mod in enterprise_plan.modules:
            ent = Entitlement(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, f"ent-{cid}-{mod}"),
                company_id=cid,
                tenant_id=cid,
                module_code=mod,
                is_enabled=True,
                source_subscription_id=sub.id
            )
            await _safe_add(session, ent, f"Entitlement: {mod} for {cid}")

# --- DB Orchestration Helpers ---
SERVICE_DB_MAP = {
    "auth": "dbname", # Auth Service (Core DB)
    "master": "master_data_db",
    "inventory": "inventory_db",
    "subscription": "subscription_db",
    "hcm": "hcm_db",
    "tickets": "tickets_db",
    "notification": "notification_db"
}

def get_session_factory(db_name: str):
    """Creates a dedicated engine and session for a specific microservice DB."""
    base_url = settings.ASYNC_DATABASE_URL
    # Logic to replace the database name in the URL safely
    # From: postgresql+asyncpg://user:pass@localhost:5433/dbname
    # To:   postgresql+asyncpg://user:pass@localhost:5433/db_name
    import re
    new_url = re.sub(r'/[a-zA-Z0-9_\-]+(\?.*)?$', f'/{db_name}\\1', base_url)
    print(f"DEBUG: Connecting to {db_name} -> {new_url}")
    
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    engine = create_async_engine(new_url, pool_pre_ping=True, echo=False)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# --- Orquestador Principal ---
async def run_unified_seed():
    log.info("=" * 55)
    log.info("   InternoCore - Unified Industrial Seed v4 [MULTI-DB]")
    log.info("=" * 55)

    # 1. Auth & Global Enum (Core DB)
    log.info("\n>>> [SECTION 1] Auth & Enumerations (Auth DB)")
    auth_factory = get_session_factory(SERVICE_DB_MAP["auth"])
    async with auth_factory() as session:
        await seed_enumerations(session)
        await seed_auth(session)
        await session.commit()

    # 2. Subscriptions
    log.info("\n>>> [SECTION 2] Subscriptions (Subscription DB)")
    sub_factory = get_session_factory(SERVICE_DB_MAP["subscription"])
    async with sub_factory() as session:
        await seed_subscriptions(session)
        await session.commit()

    # 3. Master Data
    log.info("\n>>> [SECTION 3] Master Data (Master Data DB)")
    master_factory = get_session_factory(SERVICE_DB_MAP["master"])
    async with master_factory() as session:
        await seed_enumerations(session)  # sync global enums to master_data_db for enumerations endpoint
        await seed_partners(session)
        await session.flush()
        await seed_master_data(session)
        await seed_variants_master(session)
        await session.commit()

    # 4. Inventory Core & Variants
    log.info("\n>>> [SECTION 4] Inventory & Variants (Inventory DB)")
    inv_factory = get_session_factory(SERVICE_DB_MAP["inventory"])
    async with inv_factory() as session:
        await seed_inventory(session)
        await session.commit()

    # 5. Support & HR
    log.info("\n>>> [SECTION 5] Support & HCM (Dedicated DBs)")
    tickets_factory = get_session_factory(SERVICE_DB_MAP["tickets"])
    async with tickets_factory() as session:
        await seed_tickets(session)
        await session.commit()

    hcm_factory = get_session_factory(SERVICE_DB_MAP["hcm"])
    async with hcm_factory() as session:
        await seed_industrial_identities(session)
        await session.commit()

    # [Phase 84] Customs compliance seed (inline — uses inventory_db session)
    log.info("\n>>> [SECTION 6] Customs Compliance (Inline)")
    try:
        async with inv_factory() as session:
            from datetime import timedelta
            now_utc = datetime.now(timezone.utc)
            uom_id = uuid.UUID("9e222ea8-d40b-427c-b91a-e839c4576dde")  # PZ stable ID

            for cid, cname in [
                (ENTERPRISE_ID, "Enterprise"),
                (LOGISTICS_MX_ID, "Logistics MX"),
                (LOGISTICS_US_ID, "Logistics US"),
            ]:
                # Find warehouse for this company
                wh_res = await session.execute(
                    text("SELECT id FROM inventory_warehouses WHERE company_id = :cid LIMIT 1"),
                    {"cid": cid}
                )
                wh_id = wh_res.scalar()
                if not wh_id:
                    log.warning(f"  SKIP Customs: No warehouse for {cname}")
                    continue

                for i in range(1, 4):
                    ped_num = f"24{i:02d}39547000{i}1"
                    ped_id = uuid.uuid4()
                    await session.execute(text("""
                        INSERT INTO customs_pedimentos (
                            id, pedimento_number, customs_key, operation_type, customs_date,
                            is_temporary, exchange_rate_dof,
                            company_id, tenant_id, version_id, is_active, created_at
                        ) VALUES (
                            :id, :num, 'V1', 'IMPORT', :cdate,
                            TRUE, 17.50,
                            :cid, :cid, 1, TRUE, NOW()
                        ) ON CONFLICT (pedimento_number) DO NOTHING;
                    """), {"id": ped_id, "num": ped_num, "cdate": now_utc - timedelta(days=30), "cid": cid})

                    # Resolve actual pedimento ID
                    res_p = await session.execute(
                        text("SELECT id FROM customs_pedimentos WHERE pedimento_number = :num"), {"num": ped_num}
                    )
                    actual_ped_id = res_p.scalar()

                    # Create inventory movements for each product
                    for prod in PRODUCT_CATALOG:
                        await session.execute(text("""
                            INSERT INTO inventory_movements (
                                id, product_id, warehouse_id, quantity, available_quantity,
                                movement_type, customs_pedimento_id, expiry_date,
                                uom_id, weight, unit_price, currency,
                                document_type, document_id,
                                company_id, tenant_id,
                                version_id, is_active, created_at
                            ) VALUES (
                                :id, :pid, :wid, :qty, :qty, 'IN', :ped, :exp,
                                :uom, :weight, 10.0, 'USD',
                                'INVENTORY_DOC', :did,
                                :cid, :cid, 1, TRUE, NOW()
                            ) ON CONFLICT DO NOTHING;
                        """), {
                            "id": uuid.uuid4(), "pid": prod["id"], "wid": wh_id,
                            "qty": Decimal("100.00"), "ped": actual_ped_id,
                            "exp": now_utc + timedelta(days=365),
                            "uom": uom_id, "weight": Decimal("1.0"),
                            "did": uuid.uuid4(), "cid": cid
                        })

                log.info(f"  OK Customs: {cname} (3 pedimentos, {len(PRODUCT_CATALOG)*3} movements)")

            # Normalize locations on existing movements
            await session.execute(text(
                "UPDATE inventory_movements SET location = 'SYS_RECEIVING' WHERE location IS NULL OR location = ''"
            ))
            await session.commit()
        log.info("   ✅ Customs Compliance OK.")
    except Exception as e:
        log.warning(f"Failed to run customs seed: {e}")

    log.info("\n" + "=" * 55)
    log.info("   UNIFIED SEED COMPLETED SUCCESSFULLY")
    log.info("=" * 55)

if __name__ == "__main__":
    asyncio.run(run_unified_seed())
