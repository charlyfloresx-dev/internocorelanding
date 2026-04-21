"""
Auth Service - Seed Script
==================================================
Estructura:
  - 1 BusinessGroup: Interno Global Operations
  - 3 Empresas:
      * InternoCorp Enterprise  → Charly, ADMIN_SCOPES (wildcard *)
      * Interno Logistics MX/US → Charly (MANAGER_SCOPES), Operador (OPERATOR_SCOPES)
      * Empresa Demo (Pendiente)→ Sin usuarios activos
  - Usuarios:
      * charly@interno.com  / charly123
      * operador@interno.com / ops123

NOTA: Los ROLES son solo un campo FK requerido.
      Los SCOPES en UserCompanyRole son la fuente real de accesos.
"""
import os
import sys
import asyncio
import logging
import uuid

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("seed")

# ─── App Imports ──────────────────────────────────────────────────────────────
from sqlalchemy import select, text
from auth_app.core.database import AsyncSessionLocal
from auth_app.models import BusinessGroup, Company, User, Role, UserCompanyRole
from auth_app.core.security import hash_password

# ─── IDs Fijos (idempotent) ───────────────────────────────────────────────────
GROUP_ID       = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
ENTERPRISE_ID  = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")
DEMO_ID        = uuid.UUID("203e03c9-5d65-43ff-9e83-864ef605426c")
CHARLY_ID      = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
OPERATOR_ID    = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc")
SUPERVISOR_ID  = uuid.UUID("85236974-5678-4cd2-ccbb-987654321def")

# ─── Scopes (SSOT: frontend/src/app/core/services/navigation.service.ts) ──────
# Wildcard "*" = admin bypass en el frontend (ve todo el sidebar)
ADMIN_SCOPES = ["*"]

# Manager/Logistics: Inventarios + Catálogo + WMS
MANAGER_SCOPES = [
    "inv:movements:manage", "inv:warehouse:manage",
    "master:catalog:manage",
    "wms:manage",
]

# Operador: Solo movimientos de inventario
OPERATOR_SCOPES = ["inv:movements:manage"]


async def get_or_create_role(db, name: str, company_id: uuid.UUID) -> Role:
    """Busca un rol por nombre+empresa. Si no existe, lo crea."""
    stmt = select(Role).where(Role.name == name, Role.company_id == company_id)
    role = (await db.execute(stmt)).scalar_one_or_none()
    if not role:
        role = Role(name=name, company_id=company_id, tenant_id=company_id, version_id=1, is_active=True)
        db.add(role)
        await db.flush()
    return role


async def run_seed():
    log.info("=" * 50)
    log.info("  InternoCore Auth-Service — SEED V5")
    log.info("=" * 50)

    async with AsyncSessionLocal() as db:
        try:
            # ── 1. BusinessGroup ──────────────────────────────────
            log.info("[1/5] BusinessGroup...")
            bg = await db.get(BusinessGroup, GROUP_ID)
            if not bg:
                db.add(BusinessGroup(
                    id=GROUP_ID,
                    name="Interno Global Operations",
                    version_id=1,
                    is_active=True
                ))
                await db.flush()
                log.info("  ✅ BusinessGroup creado.")
            else:
                log.info("  ℹ️  BusinessGroup ya existe.")

            # ── 2. Empresas ───────────────────────────────────────
            log.info("[2/5] Empresas...")
            companies = [
                (ENTERPRISE_ID, "Interno Enterprise",       "ACTIVE"),
                (LOGISTICS_MX_ID, "Interno Logistic MX",       "ACTIVE"),
                (LOGISTICS_US_ID, "Interno Logistic US",       "ACTIVE"),
                (DEMO_ID,       "Empresa Demo (Pendiente)",     "ACTIVE"),
            ]
            for cid, cname, cstatus in companies:
                co = await db.get(Company, cid)
                if not co:
                    db.add(Company(
                        id=cid, name=cname, status=cstatus,
                        parent_group_id=GROUP_ID,
                        version_id=1, is_active=True
                    ))
                    await db.flush()
                    log.info(f"  ✅ Empresa '{cname}' creada.")
                else:
                    co.name = cname # Forzar actualización del nombre
                    co.status = cstatus # Forzar actualización del estado
                    log.info(f"  ℹ️  Empresa '{cname}' actualizada.")

            # ── 3. Roles (solo "admin" y "operator" — FK requerida) ──
            log.info("[3/5] Roles base...")
            role_ent_admin  = await get_or_create_role(db, "admin",    ENTERPRISE_ID)
            role_log_mx_admin = await get_or_create_role(db, "admin",    LOGISTICS_MX_ID)
            role_log_mx_op    = await get_or_create_role(db, "operator", LOGISTICS_MX_ID)
            role_log_us_admin = await get_or_create_role(db, "admin",    LOGISTICS_US_ID)
            role_demo_admin   = await get_or_create_role(db, "admin",    DEMO_ID)
            log.info("  ✅ Roles OK.")

            # ── 4. Usuarios ───────────────────────────────────────
            log.info("[4/5] Usuarios...")

            # Charly — empresa principal: Enterprise
            charly = await db.get(User, CHARLY_ID)
            if not charly:
                db.add(User(
                    id=CHARLY_ID,
                    email="charly@interno.com",
                    hashed_password=hash_password("charly123"),
                    company_id=ENTERPRISE_ID,   # FK obligatoria
                    tenant_id=ENTERPRISE_ID,
                    version_id=1,
                    is_active=True
                ))
                await db.flush()
                log.info("  ✅ Usuario Charly creado.")
            else:
                log.info("  ℹ️  Charly ya existe.")

            # Charly (Google OAuth) — vinculado a las mismas empresas
            CHARLY_GOOGLE_EMAIL = "charly.flores.x@gmail.com"
            charly_google = (await db.execute(select(User).where(User.email == CHARLY_GOOGLE_EMAIL))).scalar_one_or_none()
            if not charly_google:
                charly_google = User(
                    email=CHARLY_GOOGLE_EMAIL,
                    hashed_password=None, # Solo OAuth
                    company_id=ENTERPRISE_ID,
                    tenant_id=ENTERPRISE_ID,
                    version_id=1,
                    is_active=True
                )
                db.add(charly_google)
                await db.flush()
                log.info(f"  ✅ Usuario Google '{CHARLY_GOOGLE_EMAIL}' creado.")
            else:
                log.info(f"  ℹ️  Usuario Google '{CHARLY_GOOGLE_EMAIL}' ya existe.")

            # Operador — empresa principal: Logistics
            operator = await db.get(User, OPERATOR_ID)

            if not operator:
                db.add(User(
                    id=OPERATOR_ID,
                    email="operador@interno.com",
                    hashed_password=hash_password("ops123"),
                    company_id=LOGISTICS_MX_ID,
                    tenant_id=LOGISTICS_MX_ID,
                    version_id=1,
                    is_active=True
                ))
                await db.flush()
                log.info("  ✅ Usuario Operador creado.")
            else:
                log.info("  ℹ️  Operador ya existe.")

            # Supervisor US — empresa principal: Logistics US
            supervisor = await db.get(User, SUPERVISOR_ID)
            if not supervisor:
                db.add(User(
                    id=SUPERVISOR_ID,
                    email="supervisor_us@interno.com",
                    hashed_password=hash_password("super123"),
                    company_id=LOGISTICS_US_ID,
                    tenant_id=LOGISTICS_US_ID,
                    version_id=1,
                    is_active=True
                ))
                await db.flush()
                log.info("  ✅ Usuario Supervisor US creado.")
            else:
                log.info("  ℹ️  Supervisor US ya existe.")

            # ── 5. Vinculaciones RBAC (scopes son la fuente de verdad) ──
            log.info("[5/5] Vinculaciones (UserCompanyRole)...")

            # Limpiar solo las vinculaciones de estos tres usuarios (incluyendo al de Google)
            from sqlalchemy import delete
            await db.execute(
                delete(UserCompanyRole).where(
                    UserCompanyRole.user_id.in_([CHARLY_ID, OPERATOR_ID, SUPERVISOR_ID, charly_google.id])
                )
            )
            await db.flush()

            # Charly → Enterprise (FULL ADMIN)
            db.add(UserCompanyRole(
                user_id=CHARLY_ID, company_id=ENTERPRISE_ID,
                tenant_id=ENTERPRISE_ID,
                role_id=role_ent_admin.id, scopes=ADMIN_SCOPES,
                is_new=False, version_id=1
            ))

            # Charly → Logistics MX (Inventarios + Master Data)
            db.add(UserCompanyRole(
                user_id=CHARLY_ID, company_id=LOGISTICS_MX_ID,
                tenant_id=LOGISTICS_MX_ID,
                role_id=role_log_mx_admin.id, scopes=MANAGER_SCOPES,
                is_new=False, version_id=1
            ))

            # Charly → Logistics US (Inventarios + Master Data)
            db.add(UserCompanyRole(
                user_id=CHARLY_ID, company_id=LOGISTICS_US_ID,
                tenant_id=LOGISTICS_US_ID,
                role_id=role_log_us_admin.id, scopes=MANAGER_SCOPES,
                is_new=False, version_id=1
            ))

            # Charly → Demo (Pendiente de Configuración)
            db.add(UserCompanyRole(
                user_id=CHARLY_ID, company_id=DEMO_ID,
                tenant_id=DEMO_ID,
                role_id=role_demo_admin.id, scopes=["audit:logs:view"], # Solo auditoría básica por ser pendiente
                is_new=True, version_id=1
            ))

            # Operador → Logistics MX (Solo Inventarios)
            db.add(UserCompanyRole(
                user_id=OPERATOR_ID, company_id=LOGISTICS_MX_ID,
                tenant_id=LOGISTICS_MX_ID,
                role_id=role_log_mx_op.id, scopes=OPERATOR_SCOPES,
                is_new=False, version_id=1
            ))

            # Supervisor US → Logistics US (Logistics Scopes)
            db.add(UserCompanyRole(
                user_id=SUPERVISOR_ID, company_id=LOGISTICS_US_ID,
                tenant_id=LOGISTICS_US_ID,
                role_id=role_log_us_admin.id, scopes=MANAGER_SCOPES,
                is_new=False, version_id=1
            ))

            # [GOOGLE] Charly → Enterprise (FULL ADMIN)
            db.add(UserCompanyRole(
                user_id=charly_google.id, company_id=ENTERPRISE_ID,
                tenant_id=ENTERPRISE_ID,
                role_id=role_ent_admin.id, scopes=ADMIN_SCOPES,
                is_new=False, version_id=1
            ))

            # [GOOGLE] Charly → Logistics MX (Inventarios + Master Data)
            db.add(UserCompanyRole(
                user_id=charly_google.id, company_id=LOGISTICS_MX_ID,
                tenant_id=LOGISTICS_MX_ID,
                role_id=role_log_mx_admin.id, scopes=MANAGER_SCOPES,
                is_new=False, version_id=1
            ))

            # [GOOGLE] Charly → Logistics US (Inventarios + Master Data)
            db.add(UserCompanyRole(
                user_id=charly_google.id, company_id=LOGISTICS_US_ID,
                tenant_id=LOGISTICS_US_ID,
                role_id=role_log_us_admin.id, scopes=MANAGER_SCOPES,
                is_new=False, version_id=1
            ))

            await db.commit()

            log.info("=" * 50)
            log.info("  🚀 SEED COMPLETADO EXITOSAMENTE")
            log.info("=" * 50)

        except Exception as e:
            await db.rollback()
            log.exception(f"❌ SEED FALLÓ: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
