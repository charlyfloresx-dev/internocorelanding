"""
HR Service - Seed Script
==================================================
Estructura:
  - 3 Colaboradores demo (uno por empresa):
      * Carlos Ramírez — InternoCorp Enterprise (RFID: "RFID001")
      * Luis Torres     — Interno Logistics      (RFID: "RFID002", Supervisor)
      * Ana García      — Interno Logistics      (PIN: "1234", subordinada de Luis)

  is_direct = True  → Operador de piso directo
  is_direct = False → Indirecto (administrativo, calidad, etc.)
"""
import os
import sys
import asyncio
import logging
import uuid
from datetime import date

# ─── Path Setup ───────────────────────────────────────────────────────────────
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [BACKEND_ROOT, SERVICE_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(SERVICE_ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("seed_hr")

from sqlalchemy import select
from hcm_app.core.database import AsyncSessionLocal
from hcm_app.core.security import hash_rfid, hash_pin
from hcm_app.models.collaborator import Collaborator
from hcm_app.models.department import Department
from hcm_app.models.tenant_settings import HrTenantConfig

# ─── Known Company/Tenant IDs (must match auth_service seed) ─────────────────
ENTERPRISE_ID  = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")
GROUP_ID       = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")

# ─── Demo Collaborator IDs (deterministic) ────────────────────────────────────
CARLOS_ID = uuid.UUID("11111111-0001-4001-a001-000000000001")
LUIS_ID   = uuid.UUID("11111111-0002-4001-a001-000000000002")
ANA_ID    = uuid.UUID("11111111-0003-4001-a001-000000000003")
CHARLY_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")


async def run_seed():
    log.info("=" * 50)
    log.info("  InternoCore HR-Service — SEED V1")
    log.info("=" * 50)

    async with AsyncSessionLocal() as db:
        try:
            # CREATE TABLES IF NOT EXIST
            from common.infrastructure.models.base import Base
            from hcm_app.core.database import engine
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # ── [STEP 0] Tenant Configurations (Patterns) ──
            log.info("[0/3] Seeding Tenant Configs (Patterns)...")
            configs = [
                {
                    "cid": ENTERPRISE_ID,
                    "pattern": r"^[0-9]{6}[A-Z]$", 
                    "msg": "Format Error: Enterprise IDs must be 6 digits followed by a letter (e.g., 003709A).",
                    "threshold": 15
                },
                {
                    "cid": LOGISTICS_MX_ID,
                    "pattern": r"^\d{3,6}[A-Z]?$",
                    "msg": "Format Error: Logistics IDs support 3-6 digits + optional letter (e.g., 123456A).",
                    "threshold": 30
                },
                {
                    "cid": LOGISTICS_US_ID,
                    "pattern": r"^\d{3,6}[A-Z]?$",
                    "msg": "Format Error: Logistics US IDs support 3-6 digits + optional letter (e.g., 123456A).",
                    "threshold": 5
                }
            ]
            for cfg in configs:
                q = await db.execute(select(HrTenantConfig).where(HrTenantConfig.company_id == cfg["cid"]))
                existing_cfg = q.scalar_one_or_none()
                if not existing_cfg:
                    db.add(HrTenantConfig(
                        id=uuid.uuid4(),
                        company_id=cfg["cid"],
                        tenant_id=cfg["cid"],
                        group_id=GROUP_ID,
                        internal_id_pattern=cfg["pattern"],
                        pattern_error_message=cfg["msg"],
                        cross_border_expiry_threshold_days=cfg["threshold"]
                    ))
                    log.info(f"  [OK] Config para {cfg['cid']} creada.")
                else:
                    existing_cfg.internal_id_pattern = cfg["pattern"]
                    existing_cfg.cross_border_expiry_threshold_days = cfg["threshold"]
                    log.info(f"  [INFO] Config para {cfg['cid']} actualizada.")

            # ── [STEP 0.5] Default Departments per company ────────────────────────
            log.info("[0.5/3] Seeding default departments...")
            _DEFAULT_DEPTS = [
                ("Producción",    "PROD",  "Operadores directos de línea de producción"),
                ("Calidad",       "QUAL",  "Control e inspección de calidad"),
                ("Mantenimiento", "MANT",  "Mantenimiento preventivo y correctivo de equipos"),
                ("Almacén",       "ALM",   "Recepción, almacenaje y despacho de materiales"),
                ("Administración","ADMIN", "Gestión administrativa y recursos humanos"),
                ("Ingeniería",    "ENG",   "Ingeniería de procesos y manufactura"),
            ]
            for company_id in [ENTERPRISE_ID, LOGISTICS_MX_ID, LOGISTICS_US_ID]:
                for (name, code, desc) in _DEFAULT_DEPTS:
                    dept_id = uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        f"interno.dept.{company_id}.{code}"
                    )
                    existing = await db.get(Department, dept_id)
                    if not existing:
                        db.add(Department(
                            id=dept_id,
                            company_id=company_id,
                            tenant_id=company_id,
                            group_id=GROUP_ID,
                            name=name,
                            code=code,
                            description=desc,
                            is_active=True,
                            version_id=1,
                        ))
                        log.info(f"  [OK] {name} ({code}) → {company_id}")
                    else:
                        existing.description = desc
            await db.flush()
            log.info("  [OK] Departamentos por defecto listos.")

            # ── Carlos Ramírez — Enterprise, RFID, Supervisor (sin supervisor_id) ──
            log.info("[1/3] Carlos Ramírez (Supervisor, Enterprise)...")
            carlos = await db.get(Collaborator, CARLOS_ID)
            if not carlos:
                db.add(Collaborator(
                    id=CARLOS_ID,
                    internal_id="003709A",
                    first_name="Carlos",
                    last_name_paternal="Ramírez",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{ENTERPRISE_ID}.ALM"),
                    translation_key="dept.warehouse",
                    is_direct=True,
                    supervisor_id=None,   # Top of the tree → is_supervisor=True
                    # WH-TIJ for Enterprise
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{ENTERPRISE_ID}.WH-TIJ"),
                    rfid_tag=hash_rfid("960091919"),
                    pin_code=hash_pin("1234"),
                    company_id=ENTERPRISE_ID,
                    tenant_id=ENTERPRISE_ID,
                    group_id=GROUP_ID,
                    user_id=CHARLY_ID,
                    assigned_plant="Tijuana Plant A",
                    shift="Turno Matutino",
                    version_id=1,
                ))
                await db.flush()
                log.info("  [OK] Carlos creado.")
            else:
                carlos.rfid_tag = hash_rfid("960091919")
                carlos.pin_code = hash_pin("1234")
                carlos.internal_id = "003709A"
                carlos.assigned_plant = "Tijuana Plant A"
                carlos.shift = "Turno Matutino"
                log.info("  [INFO] Carlos ya existe y credenciales actualizadas.")

            # ── Carlos Ramírez — LOGISTICS MX (Mismo RFID para probar selección) ──
            CARLOS_MX_ID = uuid.UUID("11111111-0001-4001-b001-000000000001")
            log.info("[1.1/3] Carlos Ramírez (Logistics MX, SAME RFID)...")
            carlos_mx = await db.get(Collaborator, CARLOS_MX_ID)
            if not carlos_mx:
                db.add(Collaborator(
                    id=CARLOS_MX_ID,
                    internal_id="003709A",
                    first_name="Carlos",
                    last_name_paternal="Ramírez",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{LOGISTICS_MX_ID}.ALM"),
                    translation_key="dept.warehouse",
                    is_direct=True,
                    supervisor_id=None,
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_MX_ID}.WH-TIJ"),
                    rfid_tag=hash_rfid("960091919"),
                    pin_code=hash_pin("1234"),
                    company_id=LOGISTICS_MX_ID,
                    tenant_id=LOGISTICS_MX_ID,
                    group_id=GROUP_ID,
                    user_id=CHARLY_ID,
                    assigned_plant="Tijuana Logistics Hub",
                    shift="Turno Vespertino",
                    # Cross-border credentials (active CDL and medical, but missing sentry/GE to test failure)
                    driver_license_number="CDL-MX-88",
                    driver_license_expiry=date(2027, 12, 31),
                    medical_certificate_expiry=date(2027, 12, 31),
                    visa_number="VISA-MX-88",
                    visa_expiry=date(2027, 12, 31),
                    version_id=1,
                ))
                log.info("  [OK] Carlos (Logistic MX) creado.")
            else:
                carlos_mx.assigned_plant = "Tijuana Logistics Hub"
                carlos_mx.shift = "Turno Vespertino"
                carlos_mx.driver_license_expiry = date(2027, 12, 31)
                carlos_mx.medical_certificate_expiry = date(2027, 12, 31)
                carlos_mx.visa_expiry = date(2027, 12, 31)

            # ── Carlos Ramírez — LOGISTICS US (Tercera Identidad) ──
            CARLOS_US_ID = uuid.UUID("11111111-0001-4001-c001-000000000001")
            log.info("[1.2/3] Carlos Ramírez (Logistics US, SAME RFID)...")
            carlos_us = await db.get(Collaborator, CARLOS_US_ID)
            if not carlos_us:
                db.add(Collaborator(
                    id=CARLOS_US_ID,
                    internal_id="003709A",
                    first_name="Carlos",
                    last_name_paternal="Ramírez",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{LOGISTICS_US_ID}.ALM"),
                    translation_key="dept.warehouse",
                    is_direct=True,
                    supervisor_id=None,
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_US_ID}.WH-SDY"),
                    rfid_tag=hash_rfid("960091919"),
                    pin_code=hash_pin("1234"),
                    company_id=LOGISTICS_US_ID,
                    tenant_id=LOGISTICS_US_ID,
                    group_id=GROUP_ID,
                    user_id=CHARLY_ID,
                    assigned_plant="San Diego WH",
                    shift="Turno Nocturno",
                    # Fully compliant cross-border operator (Global Entry active)
                    global_entry_id="GE-US-777",
                    driver_license_number="CDL-US-77",
                    driver_license_expiry=date(2027, 12, 31),
                    medical_certificate_expiry=date(2027, 12, 31),
                    visa_number="VISA-US-77",
                    visa_expiry=date(2027, 12, 31),
                    version_id=1,
                ))
                log.info("  [OK] Carlos (Logistic US) creado.")
            else:
                carlos_us.assigned_plant = "San Diego WH"
                carlos_us.shift = "Turno Nocturno"
                carlos_us.global_entry_id = "GE-US-777"
                carlos_us.driver_license_expiry = date(2027, 12, 31)
                carlos_us.medical_certificate_expiry = date(2027, 12, 31)
                carlos_us.visa_expiry = date(2027, 12, 31)

            # ── Luis Torres — Logistics MX (RFID, Supervisor) ──
            log.info("[2/3] Luis Torres (Supervisor, Logistics MX)...")
            luis = await db.get(Collaborator, LUIS_ID)
            if not luis:
                db.add(Collaborator(
                    id=LUIS_ID,
                    internal_id="201",
                    first_name="Luis",
                    last_name_paternal="Torres",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{LOGISTICS_MX_ID}.PROD"),
                    translation_key="dept.logistics",
                    is_direct=True,
                    supervisor_id=None,   # Supervisor
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_MX_ID}.WH-TIJ"),
                    rfid_tag=hash_rfid("2327559684"),
                    pin_code=None,
                    company_id=LOGISTICS_MX_ID,
                    tenant_id=LOGISTICS_MX_ID,
                    group_id=GROUP_ID,
                    assigned_plant="Tijuana Logistics Hub",
                    shift="Turno Matutino",
                    # Fully compliant cross-border operator (Sentry active)
                    sentry_id="SENTRY-MX-123",
                    driver_license_number="CDL-MX-123",
                    driver_license_expiry=date(2027, 12, 31),
                    medical_certificate_expiry=date(2027, 12, 31),
                    visa_number="VISA-MX-123",
                    visa_expiry=date(2027, 12, 31),
                    version_id=1,
                ))
                await db.flush()
                log.info("  [OK] Luis creado.")
            else:
                luis.rfid_tag = hash_rfid("2327559684")
                luis.internal_id = "201"
                luis.company_id = LOGISTICS_MX_ID
                luis.tenant_id = LOGISTICS_MX_ID
                luis.home_warehouse_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_MX_ID}.WH-TIJ")
                luis.assigned_plant = "Tijuana Logistics Hub"
                luis.shift = "Turno Matutino"
                luis.sentry_id = "SENTRY-MX-123"
                luis.driver_license_expiry = date(2027, 12, 31)
                luis.medical_certificate_expiry = date(2027, 12, 31)
                luis.visa_expiry = date(2027, 12, 31)
                log.info("  [INFO] Luis ya existe y rfid actualizado.")

            # ── Luis Torres — ENTERPRISE (Mismo RFID para probar selección) ──
            LUIS_ENT_ID = uuid.UUID("11111111-0002-4001-e001-000000000002")
            log.info("[4/3] Luis Torres (Enterprise Identity, SAME RFID)...")
            luis_ent = await db.get(Collaborator, LUIS_ENT_ID)
            if not luis_ent:
                db.add(Collaborator(
                    id=LUIS_ENT_ID,
                    internal_id="901",
                    first_name="Luis",
                    last_name_paternal="Torres",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{ENTERPRISE_ID}.ALM"),
                    translation_key="dept.warehouse",
                    is_direct=True,
                    supervisor_id=None,
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{ENTERPRISE_ID}.WH-TIJ"),
                    rfid_tag=hash_rfid("2327559684"),
                    pin_code=None,
                    company_id=ENTERPRISE_ID,
                    tenant_id=ENTERPRISE_ID,
                    group_id=GROUP_ID,
                    assigned_plant="Tijuana Plant A",
                    shift="Turno Matutino",
                    version_id=1,
                ))
                await db.flush()
                log.info("  [OK] Luis (Enterprise) creado.")
            else:
                luis_ent.assigned_plant = "Tijuana Plant A"
                luis_ent.shift = "Turno Matutino"

            # ── Luis Torres — LOGISTIC US (Tercera Identidad) ──
            LUIS_US_ID = uuid.UUID("11111111-0002-4001-c001-000000000002")
            log.info("[5/3] Luis Torres (Logistic US Identity, SAME RFID)...")
            luis_us = await db.get(Collaborator, LUIS_US_ID)
            if not luis_us:
                db.add(Collaborator(
                    id=LUIS_US_ID,
                    internal_id="801",
                    first_name="Luis",
                    last_name_paternal="Torres",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{LOGISTICS_US_ID}.PROD"),
                    translation_key="dept.logistics",
                    is_direct=True,
                    supervisor_id=None,
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_US_ID}.WH-SDY"),
                    rfid_tag=hash_rfid("2327559684"),
                    pin_code=None,
                    company_id=LOGISTICS_US_ID,
                    tenant_id=LOGISTICS_US_ID,
                    group_id=GROUP_ID,
                    assigned_plant="San Diego WH",
                    shift="Turno Matutino",
                    version_id=1,
                ))
                await db.flush()
                log.info("  [OK] Luis (USA) creado.")
            else:
                luis_us.assigned_plant = "San Diego WH"
                luis_us.shift = "Turno Matutino"

            # ── Ana García — Logistics MX, PIN, subordinada de Luis ──
            log.info("[3/3] Ana García (Operadora, subordinada de Luis)...")
            ana = await db.get(Collaborator, ANA_ID)
            if not ana:
                db.add(Collaborator(
                    id=ANA_ID,
                    internal_id="301",
                    first_name="Ana",
                    last_name_paternal="García",
                    department_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.dept.{LOGISTICS_MX_ID}.ALM"),
                    translation_key="dept.warehouse",
                    is_direct=True,
                    supervisor_id=LUIS_ID,   # Reports to Luis → is_supervisor=False
                    # WH-TIJ for Logistics MX
                    home_warehouse_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_MX_ID}.WH-TIJ"),
                    rfid_tag=None,
                    pin_code=hash_pin("1234"),
                    company_id=LOGISTICS_MX_ID,
                    tenant_id=LOGISTICS_MX_ID,
                    group_id=GROUP_ID,
                    assigned_plant="Tijuana Logistics Hub",
                    shift="Turno Matutino",
                    version_id=1,
                ))
                await db.flush()
                log.info("  [OK] Ana creada.");
            else:
                ana.internal_id = "301"
                ana.company_id = LOGISTICS_MX_ID
                ana.tenant_id = LOGISTICS_MX_ID
                ana.home_warehouse_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{LOGISTICS_MX_ID}.WH-TIJ")
                ana.assigned_plant = "Tijuana Logistics Hub"
                ana.shift = "Turno Matutino"
                log.info("  [INFO] Ana ya existe.")

            await db.commit()
            log.info("=" * 50)
            log.info("  HR SEED COMPLETADO")
            log.info("  RFID Credentials:")
            log.info("    Carlos (Enterprise): scan '960091919' (Charly's Card)")
            log.info("    Luis   (Logistics) : scan '2327559684' (Operador's Card)")
            log.info("    Ana    (Logistics) : PIN  '1234'")
            log.info("=" * 50)

        except Exception as e:
            await db.rollback()
            log.exception(f"ERROR: HR SEED FALLO: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
