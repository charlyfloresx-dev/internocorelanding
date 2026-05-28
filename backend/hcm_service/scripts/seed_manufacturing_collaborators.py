"""
Manufacturing Collaborators - Seed Script
==================================================
Genera un set de datos realista para una empresa de manufactura tradicional multi-tenant,
creando primero los departamentos relacionales y luego vinculando los colaboradores a ellos:
1. Operaciones / Producción (Gerente de Planta, Supervisores, Operadores, Ensambladores)
2. Mantenimiento (Jefe de Mantenimiento, Técnicos)
3. Calidad (Auditor, Inspector)
4. Logística y Almacén (Gerente, Montacarguistas, Auxiliares)
5. Recursos Humanos (Coordinador de Nómina, Generalista)
6. Sistemas / TI (Administrador de Soporte, Ingeniero)
7. Compras / Supply Chain (Comprador Senior, Especialista)

Se siembran registros para dos empresas:
- La empresa muestra genérica (sample_company_id = "00000000-0000-0000-0000-000000000001")
- La empresa principal activa (enterprise_company_id = "9cd9986b-89da-48b7-8733-26a2a1225b01")
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
log = logging.getLogger("seed_manufacturing_hr")

from sqlalchemy import select
from hcm_app.core.database import AsyncSessionLocal
from hcm_app.core.security import hash_rfid, hash_pin
from hcm_app.models.collaborator import Collaborator
from hcm_app.models.department import Department

# ─── Multi-Tenant Configurations ──────────────────────────────────────────────
SAMPLE_COMPANY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ENTERPRISE_COMPANY_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
GROUP_ID = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")

# Diccionario para mapear claves de traducción a códigos de departamento relacionales
KEY_TO_CODE = {
    "dept.production": "PRODUCTION",
    "dept.maintenance": "MAINTENANCE",
    "dept.quality": "QUALITY",
    "dept.warehouse": "WMS",
    "dept.hr": "HR",
    "dept.it": "IT",
    "dept.purchasing": "PURCHASING"
}

# Departamentos a sembrar
DEPARTMENTS_TEMPLATE = [
    {"code": "PRODUCTION", "name": "Producción"},
    {"code": "MAINTENANCE", "name": "Mantenimiento"},
    {"code": "QUALITY", "name": "Calidad"},
    {"code": "WMS", "name": "Almacén"},
    {"code": "HR", "name": "Recursos Humanos"},
    {"code": "IT", "name": "Sistemas"},
    {"code": "PURCHASING", "name": "Compras"}
]

# Colaboradores a sembrar
COLLABORATORS_TEMPLATE = [
    # 1. Operaciones / Producción
    {
        "internal_id": "OP1001",
        "first_name": "Mauricio",
        "last_name": "López",
        "translation_key": "dept.production",
        "job_title": "Gerente de Planta",
        "is_direct": False,
        "rfid_tag": "rfid_op_01",
        "pin_code": "4321",
        "is_supervisor": True
    },
    {
        "internal_id": "OP1002",
        "first_name": "Eduardo",
        "last_name": "Gómez",
        "translation_key": "dept.production",
        "job_title": "Supervisor de Turno A",
        "is_direct": True,
        "rfid_tag": "rfid_op_02",
        "pin_code": "1111",
        "is_supervisor": True
    },
    {
        "internal_id": "OP1003",
        "first_name": "Sofía",
        "last_name": "Herrera",
        "translation_key": "dept.production",
        "job_title": "Supervisor de Turno B",
        "is_direct": True,
        "rfid_tag": "rfid_op_03",
        "pin_code": "2222",
        "is_supervisor": True
    },
    {
        "internal_id": "OP1004",
        "first_name": "Daniel",
        "last_name": "Sánchez",
        "translation_key": "dept.production",
        "job_title": "Operador de Maquinaria",
        "is_direct": True,
        "rfid_tag": "rfid_op_04",
        "pin_code": "1234",
        "is_supervisor": False
    },
    {
        "internal_id": "OP1005",
        "first_name": "Valeria",
        "last_name": "Castillo",
        "translation_key": "dept.production",
        "job_title": "Técnico de Ensamblaje",
        "is_direct": True,
        "rfid_tag": "rfid_op_05",
        "pin_code": "1234",
        "is_supervisor": False
    },

    # 2. Mantenimiento
    {
        "internal_id": "MN2001",
        "first_name": "Roberto",
        "last_name": "Mendoza",
        "translation_key": "dept.maintenance",
        "job_title": "Jefe de Mantenimiento",
        "is_direct": False,
        "rfid_tag": "rfid_mn_01",
        "pin_code": "1234",
        "is_supervisor": True
    },
    {
        "internal_id": "MN2002",
        "first_name": "Javier",
        "last_name": "Ríos",
        "translation_key": "dept.maintenance",
        "job_title": "Técnico Electromecánico Senior",
        "is_direct": True,
        "rfid_tag": "rfid_mn_02",
        "pin_code": "1234",
        "is_supervisor": False
    },
    {
        "internal_id": "MN2003",
        "first_name": "Andrés",
        "last_name": "Pérez",
        "translation_key": "dept.maintenance",
        "job_title": "Técnico Electromecánico Junior",
        "is_direct": True,
        "rfid_tag": "rfid_mn_03",
        "pin_code": "1234",
        "is_supervisor": False
    },

    # 3. Calidad
    {
        "internal_id": "QL3001",
        "first_name": "Gabriela",
        "last_name": "Martínez",
        "translation_key": "dept.quality",
        "job_title": "Auditor de Calidad",
        "is_direct": False,
        "rfid_tag": "rfid_ql_01",
        "pin_code": "1234",
        "is_supervisor": False
    },
    {
        "internal_id": "QL3002",
        "first_name": "Ricardo",
        "last_name": "Torres",
        "translation_key": "dept.quality",
        "job_title": "Inspector de Línea",
        "is_direct": True,
        "rfid_tag": "rfid_ql_02",
        "pin_code": "1234",
        "is_supervisor": False
    },

    # 4. Logística y Almacén (WMS)
    {
        "internal_id": "LG4001",
        "first_name": "Fernando",
        "last_name": "Morales",
        "translation_key": "dept.warehouse",
        "job_title": "Gerente de Almacén",
        "is_direct": False,
        "rfid_tag": "rfid_lg_01",
        "pin_code": "1234",
        "is_supervisor": True
    },
    {
        "internal_id": "LG4002",
        "first_name": "Hugo",
        "last_name": "Vargas",
        "translation_key": "dept.warehouse",
        "job_title": "Montacarguista Senior",
        "is_direct": True,
        "rfid_tag": "rfid_lg_02",
        "pin_code": "1234",
        "is_supervisor": False
    },
    {
        "internal_id": "LG4003",
        "first_name": "Lorena",
        "last_name": "Reyes",
        "translation_key": "dept.warehouse",
        "job_title": "Auxiliar de Recibo/Envío",
        "is_direct": True,
        "rfid_tag": "rfid_lg_03",
        "pin_code": "1234",
        "is_supervisor": False
    },

    # 5. Recursos Humanos
    {
        "internal_id": "HR5001",
        "first_name": "Beatriz",
        "last_name": "Luna",
        "translation_key": "dept.hr",
        "job_title": "Coordinador de Nómina",
        "is_direct": False,
        "rfid_tag": "rfid_hr_01",
        "pin_code": "1234",
        "is_supervisor": False
    },
    {
        "internal_id": "HR5002",
        "first_name": "Diana",
        "last_name": "Flores",
        "translation_key": "dept.hr",
        "job_title": "Generalista de Recursos Humanos",
        "is_direct": False,
        "rfid_tag": "rfid_hr_02",
        "pin_code": "1234",
        "is_supervisor": False
    },

    # 6. Sistemas / TI
    {
        "internal_id": "IT6001",
        "first_name": "Carlos",
        "last_name": "Ortiz",
        "translation_key": "dept.it",
        "job_title": "Administrador de Soporte (Helpdesk)",
        "is_direct": False,
        "rfid_tag": "rfid_it_01",
        "pin_code": "1234",
        "is_supervisor": True
    },
    {
        "internal_id": "IT6002",
        "first_name": "Arturo",
        "last_name": "Silva",
        "translation_key": "dept.it",
        "job_title": "Ingeniero de Infraestructura",
        "is_direct": False,
        "rfid_tag": "rfid_it_02",
        "pin_code": "1234",
        "is_supervisor": False
    },

    # 7. Compras / Supply Chain
    {
        "internal_id": "SC7001",
        "first_name": "Isabel",
        "last_name": "Guerra",
        "translation_key": "dept.purchasing",
        "job_title": "Comprador Senior",
        "is_direct": False,
        "rfid_tag": "rfid_sc_01",
        "pin_code": "1234",
        "is_supervisor": False
    },
    {
        "internal_id": "SC7002",
        "first_name": "Patricia",
        "last_name": "Nájera",
        "translation_key": "dept.purchasing",
        "job_title": "Especialista en Comercio Exterior",
        "is_direct": False,
        "rfid_tag": "rfid_sc_02",
        "pin_code": "1234",
        "is_supervisor": False
    }
]

async def seed_manufacturing_collaborators():
    log.info("=" * 60)
    log.info("  InternoCore HR-Service — SEMBRADO DE OPERACIONES INDUSTRIALES")
    log.info("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # 1. Asegurar que las tablas existen
            from common.infrastructure.models.base import Base
            from hcm_app.core.database import engine
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            companies_to_seed = [
                ("Muestra Genérica", SAMPLE_COMPANY_ID),
                ("InternoCorp Enterprise", ENTERPRISE_COMPANY_ID)
            ]

            for company_name, company_uuid in companies_to_seed:
                log.info(f"Sembrando departamentos y colaboradores para la compañía: '{company_name}' ({company_uuid})")

                # --- Paso 1: Sembrar Departamentos ---
                departments_by_code = {}
                for dept_tpl in DEPARTMENTS_TEMPLATE:
                    # Verificar si existe
                    q = await db.execute(
                        select(Department).where(
                            Department.code == dept_tpl["code"],
                            Department.company_id == company_uuid
                        )
                    )
                    existing_dept = q.scalar_one_or_none()

                    if not existing_dept:
                        dept_id = uuid.uuid4()
                        d = Department(
                            id=dept_id,
                            code=dept_tpl["code"],
                            name=dept_tpl["name"],
                            is_active=True,
                            company_id=company_uuid,
                            tenant_id=company_uuid,
                            version_id=1
                        )
                        db.add(d)
                        departments_by_code[dept_tpl["code"]] = dept_id
                        log.info(f"  [OK] Departamento '{d.name}' ({d.code}) preparado.")
                    else:
                        departments_by_code[dept_tpl["code"]] = existing_dept.id
                        log.info(f"  [INFO] Departamento '{existing_dept.name}' ({existing_dept.code}) ya existe.")

                await db.flush()

                # Diccionario para enlazar supervisores dinámicamente en el lote
                supervisors_by_title = {}
                collaborators_to_insert = []

                # --- Paso 2: Sembrar Supervisores Primero (para referenciarlos recursivamente) ---
                for template in COLLABORATORS_TEMPLATE:
                    if not template["is_supervisor"]:
                        continue

                    # Verificar si existe
                    q = await db.execute(
                        select(Collaborator).where(
                            Collaborator.internal_id == template["internal_id"],
                            Collaborator.company_id == company_uuid
                        )
                    )
                    existing = q.scalar_one_or_none()

                    if not existing:
                        collab_id = uuid.uuid4()
                        dept_code = KEY_TO_CODE.get(template["translation_key"])
                        dept_id = departments_by_code.get(dept_code)

                        c = Collaborator(
                            id=collab_id,
                            internal_id=template["internal_id"],
                            first_name=template["first_name"],
                            last_name_paternal=template["last_name"],
                            department_id=dept_id,
                            translation_key=template["translation_key"],
                            job_title=template["job_title"],
                            is_direct=template["is_direct"],
                            is_active=True,
                            supervisor_id=None,
                            rfid_tag=hash_rfid(template["rfid_tag"]) if template["rfid_tag"] else None,
                            pin_code=hash_pin(template["pin_code"]) if template["pin_code"] else None,
                            company_id=company_uuid,
                            tenant_id=company_uuid,
                            group_id=GROUP_ID,
                            assigned_plant="Tijuana Plant A" if company_uuid == ENTERPRISE_COMPANY_ID else "Sample Plant 1",
                            shift="Turno A" if "Turno A" in template["job_title"] else ("Turno B" if "Turno B" in template["job_title"] else "Turno Matutino"),
                            version_id=1
                        )
                        db.add(c)
                        supervisors_by_title[template["job_title"]] = collab_id
                        log.info(f"  [OK] Supervisor '{c.full_name}' ({template['job_title']}) preparado.")
                    else:
                        dept_code = KEY_TO_CODE.get(template["translation_key"])
                        dept_id = departments_by_code.get(dept_code)
                        existing.department_id = dept_id
                        existing.assigned_plant = "Tijuana Plant A" if company_uuid == ENTERPRISE_COMPANY_ID else "Sample Plant 1"
                        existing.shift = "Turno A" if "Turno A" in template["job_title"] else ("Turno B" if "Turno B" in template["job_title"] else "Turno Matutino")
                        supervisors_by_title[template["job_title"]] = existing.id
                        log.info(f"  [INFO] Supervisor '{existing.full_name}' ({template['job_title']}) migrado/actualizado.")

                await db.flush()

                # --- Paso 3: Sembrar Operativos y Enlazarlos a sus Supervisores ---
                for template in COLLABORATORS_TEMPLATE:
                    if template["is_supervisor"]:
                        continue

                    # Verificar si existe
                    q = await db.execute(
                        select(Collaborator).where(
                            Collaborator.internal_id == template["internal_id"],
                            Collaborator.company_id == company_uuid
                        )
                    )
                    existing = q.scalar_one_or_none()

                    if not existing:
                        # Determinar supervisor id
                        supervisor_id = None
                        dept_code = KEY_TO_CODE.get(template["translation_key"])
                        dept_id = departments_by_code.get(dept_code)

                        if dept_code == "PRODUCTION":
                            supervisor_id = supervisors_by_title.get("Supervisor de Turno A")
                        elif dept_code == "MAINTENANCE":
                            supervisor_id = supervisors_by_title.get("Jefe de Mantenimiento")
                        elif dept_code == "WMS":
                            supervisor_id = supervisors_by_title.get("Gerente de Almacén")
                        elif dept_code == "IT":
                            supervisor_id = supervisors_by_title.get("Administrador de Soporte (Helpdesk)")

                        collab_id = uuid.uuid4()
                        c = Collaborator(
                            id=collab_id,
                            internal_id=template["internal_id"],
                            first_name=template["first_name"],
                            last_name_paternal=template["last_name"],
                            department_id=dept_id,
                            translation_key=template["translation_key"],
                            job_title=template["job_title"],
                            is_direct=template["is_direct"],
                            is_active=True,
                            supervisor_id=supervisor_id,
                            rfid_tag=hash_rfid(template["rfid_tag"]) if template["rfid_tag"] else None,
                            pin_code=hash_pin(template["pin_code"]) if template["pin_code"] else None,
                            company_id=company_uuid,
                            tenant_id=company_uuid,
                            group_id=GROUP_ID,
                            assigned_plant="Tijuana Plant A" if company_uuid == ENTERPRISE_COMPANY_ID else "Sample Plant 1",
                            shift="Turno A" if "Turno A" in template["job_title"] else ("Turno B" if "Turno B" in template["job_title"] else "Turno Matutino"),
                            version_id=1
                        )
                        collaborators_to_insert.append(c)
                        log.info(f"  [OK] Operativo '{c.full_name}' ({template['job_title']}) preparado.")
                    else:
                        dept_code = KEY_TO_CODE.get(template["translation_key"])
                        dept_id = departments_by_code.get(dept_code)
                        
                        supervisor_id = None
                        if dept_code == "PRODUCTION":
                            supervisor_id = supervisors_by_title.get("Supervisor de Turno A")
                        elif dept_code == "MAINTENANCE":
                            supervisor_id = supervisors_by_title.get("Jefe de Mantenimiento")
                        elif dept_code == "WMS":
                            supervisor_id = supervisors_by_title.get("Gerente de Almacén")
                        elif dept_code == "IT":
                            supervisor_id = supervisors_by_title.get("Administrador de Soporte (Helpdesk)")
                        
                        existing.department_id = dept_id
                        existing.supervisor_id = supervisor_id
                        existing.assigned_plant = "Tijuana Plant A" if company_uuid == ENTERPRISE_COMPANY_ID else "Sample Plant 1"
                        existing.shift = "Turno A" if "Turno A" in template["job_title"] else ("Turno B" if "Turno B" in template["job_title"] else "Turno Matutino")
                        log.info(f"  [INFO] Operativo '{existing.full_name}' ({template['job_title']}) migrado/actualizado.")

                if collaborators_to_insert:
                    db.add_all(collaborators_to_insert)
                    await db.flush()

            await db.commit()
            log.info("=" * 60)
            log.info("  SEMILLA DE MANUFACTURA COMPLETADA SATISFACTORIAMENTE")
            log.info("=" * 60)

        except Exception as e:
            await db.rollback()
            log.exception(f"ERROR: EL SEMBRADO DE OPERACIONES FALLÓ: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_manufacturing_collaborators())
