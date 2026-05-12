"""
Auth Service - Seed Script v6 (M:1:M Identity)
==================================================
Estructura:
  - 1 BusinessGroup: Interno Global Operations
  - 4 Empresas: Enterprise, Planta MX, Planta US, Demo
  - Usuarios (User global) + Credenciales (UserCredential):
      * charly@interno.com      / charly123  -> Admin en todas las empresas
      * operador@interno.com    / ops123     -> Operator en Planta MX
      * supervisor_us@interno.com / super123 -> Manager en Planta US
      * charly.flores.x@gmail.com (Google OAuth) -> Admin en todas

NOTA: User es identidad global. Email y password viven en UserCredential.
      Los SCOPES en UserCompanyRole son la fuente real de accesos.
"""
import os
import sys
import asyncio
import logging
import uuid

# Path Setup
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
log = logging.getLogger("seed")

from sqlalchemy import select, delete
from common.infrastructure.database import AsyncSessionLocal
from auth_app.models import BusinessGroup, Company, User, Role, UserCompanyRole
from auth_app.models.user_credential import UserCredential
from auth_app.core.security import hash_password

GROUP_ID         = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
ENTERPRISE_ID    = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_MX_ID  = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
LOGISTICS_US_ID  = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")
DEMO_ID          = uuid.UUID("203e03c9-5d65-43ff-9e83-864ef605426c")
CHARLY_ID        = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
OPERATOR_ID      = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc")
SUPERVISOR_ID    = uuid.UUID("85236974-5678-4cd2-ccbb-987654321def")
CHARLY_GOOGLE_ID = uuid.UUID("11223344-aaaa-4bb1-cccc-ddeeff001122")

ADMIN_SCOPES    = ["*", "investments:manage", "investments:admin", "master:catalog:manage", "inv:movements:manage"]
MANAGER_SCOPES  = ["inv:movements:manage", "inv:warehouse:manage", "master:catalog:manage", "wms:manage", "investments:manage"]
OPERATOR_SCOPES = ["inv:movements:manage"]


async def get_or_create_role(db, name: str, company_id: uuid.UUID) -> Role:
    stmt = select(Role).where(Role.name == name, Role.company_id == company_id)
    role = (await db.execute(stmt)).scalar_one_or_none()
    if not role:
        role = Role(name=name, company_id=company_id, tenant_id=company_id, version_id=1, is_active=True)
        db.add(role)
        await db.flush()
    return role


async def get_or_create_user(db, user_id: uuid.UUID, first_name: str, last_name: str) -> User:
    user = await db.get(User, user_id)
    if not user:
        user = User(id=user_id, first_name=first_name, last_name_pat=last_name,
                    is_biometric_enabled=False, is_active=True, version_id=1)
        db.add(user)
        await db.flush()
        log.info(f"  OK User '{first_name} {last_name}' creado.")
    else:
        log.info(f"  -- User '{first_name}' ya existe.")
    return user


async def get_or_create_credential(db, user_id: uuid.UUID, email: str, credential_type: str, password: str = None) -> UserCredential:
    stmt = select(UserCredential).where(UserCredential.user_id == user_id, UserCredential.email == email)
    cred = (await db.execute(stmt)).scalar_one_or_none()
    if not cred:
        cred = UserCredential(
            user_id=user_id, email=email, credential_type=credential_type,
            hashed_password=hash_password(password) if password else None,
            is_active=True, version_id=1
        )
        db.add(cred)
        await db.flush()
        log.info(f"  OK Credencial '{email}' ({credential_type}) creada.")
    else:
        log.info(f"  -- Credencial '{email}' ya existe.")
    return cred


async def run_seed():
    log.info("=" * 50)
    log.info("  InternoCore Auth-Service - SEED V6 (M:1:M)")
    log.info("=" * 50)

    async with AsyncSessionLocal() as db:
        try:
            # 1. BusinessGroup
            log.info("[1/6] BusinessGroup...")
            bg = await db.get(BusinessGroup, GROUP_ID)
            if not bg:
                db.add(BusinessGroup(id=GROUP_ID, name="Interno Global Operations", version_id=1, is_active=True))
                await db.flush()
                log.info("  OK BusinessGroup creado.")
            else:
                log.info("  -- BusinessGroup ya existe.")

            # 2. Empresas
            log.info("[2/6] Empresas...")
            companies_data = [
                (ENTERPRISE_ID,   "Interno Enterprise",       "ACTIVE"),
                (LOGISTICS_MX_ID, "Planta MX",                "ACTIVE"),
                (LOGISTICS_US_ID, "Planta US",                "ACTIVE"),
                (DEMO_ID,         "Demo Operativo S.A.",      "ACTIVE"),
            ]
            for cid, cname, cstatus in companies_data:
                co = await db.get(Company, cid)
                if not co:
                    db.add(Company(id=cid, name=cname, status=cstatus, parent_group_id=GROUP_ID, version_id=1, is_active=True))
                    await db.flush()
                    log.info(f"  OK Empresa '{cname}' creada.")
                else:
                    co.name = cname
                    co.status = cstatus
                    log.info(f"  -- Empresa '{cname}' actualizada.")

            # 3. Roles
            log.info("[3/6] Roles...")
            role_ent_admin    = await get_or_create_role(db, "admin",    ENTERPRISE_ID)
            role_log_mx_admin = await get_or_create_role(db, "admin",    LOGISTICS_MX_ID)
            role_log_mx_op    = await get_or_create_role(db, "operator", LOGISTICS_MX_ID)
            role_log_us_admin = await get_or_create_role(db, "admin",    LOGISTICS_US_ID)
            role_demo_admin   = await get_or_create_role(db, "admin",    DEMO_ID)
            log.info("  OK Roles listos.")

            # 4. Users (identidad global — sin email ni password)
            log.info("[4/6] Users (identidad global)...")
            await get_or_create_user(db, CHARLY_ID,       "Charly",     "Flores")
            await get_or_create_user(db, OPERATOR_ID,     "Operador",   "Demo")
            await get_or_create_user(db, SUPERVISOR_ID,   "Supervisor", "US")
            await get_or_create_user(db, CHARLY_GOOGLE_ID,"Charly",     "Flores Google")

            # 5. UserCredentials (email + password / OAuth)
            log.info("[5/6] Credenciales...")
            await get_or_create_credential(db, CHARLY_ID,        "charly@interno.com",         "PASSWORD", "charly123")
            await get_or_create_credential(db, OPERATOR_ID,      "operador@interno.com",       "PASSWORD", "ops123")
            await get_or_create_credential(db, SUPERVISOR_ID,    "supervisor_us@interno.com",  "PASSWORD", "super123")
            await get_or_create_credential(db, CHARLY_GOOGLE_ID, "charly.flores.x@gmail.com",  "GOOGLE")

            # 6. UserCompanyRole (vinculacion multitenant)
            log.info("[6/6] Vinculaciones (UserCompanyRole)...")
            all_ids = [CHARLY_ID, OPERATOR_ID, SUPERVISOR_ID, CHARLY_GOOGLE_ID]
            await db.execute(delete(UserCompanyRole).where(UserCompanyRole.user_id.in_(all_ids)))
            await db.flush()

            for ucr in [
                UserCompanyRole(user_id=CHARLY_ID, company_id=ENTERPRISE_ID,   tenant_id=ENTERPRISE_ID,   role_id=role_ent_admin.id,    scopes=ADMIN_SCOPES,         is_new=False, version_id=1),
                UserCompanyRole(user_id=CHARLY_ID, company_id=LOGISTICS_MX_ID, tenant_id=LOGISTICS_MX_ID, role_id=role_log_mx_admin.id, scopes=MANAGER_SCOPES,       is_new=False, version_id=1),
                UserCompanyRole(user_id=CHARLY_ID, company_id=LOGISTICS_US_ID, tenant_id=LOGISTICS_US_ID, role_id=role_log_us_admin.id, scopes=MANAGER_SCOPES,       is_new=False, version_id=1),
                UserCompanyRole(user_id=CHARLY_ID, company_id=DEMO_ID,         tenant_id=DEMO_ID,         role_id=role_demo_admin.id,   scopes=["master:catalog:manage", "inv:movements:manage", "tickets:manage", "tickets:view"],  is_new=True,  version_id=1),
                UserCompanyRole(user_id=OPERATOR_ID,      company_id=LOGISTICS_MX_ID, tenant_id=LOGISTICS_MX_ID, role_id=role_log_mx_op.id,    scopes=OPERATOR_SCOPES, is_new=False, version_id=1),
                UserCompanyRole(user_id=SUPERVISOR_ID,    company_id=LOGISTICS_US_ID, tenant_id=LOGISTICS_US_ID, role_id=role_log_us_admin.id, scopes=MANAGER_SCOPES,  is_new=False, version_id=1),
                UserCompanyRole(user_id=CHARLY_GOOGLE_ID, company_id=ENTERPRISE_ID,   tenant_id=ENTERPRISE_ID,   role_id=role_ent_admin.id,    scopes=ADMIN_SCOPES,    is_new=False, version_id=1),
                UserCompanyRole(user_id=CHARLY_GOOGLE_ID, company_id=LOGISTICS_MX_ID, tenant_id=LOGISTICS_MX_ID, role_id=role_log_mx_admin.id, scopes=MANAGER_SCOPES,  is_new=False, version_id=1),
                UserCompanyRole(user_id=CHARLY_GOOGLE_ID, company_id=LOGISTICS_US_ID, tenant_id=LOGISTICS_US_ID, role_id=role_log_us_admin.id, scopes=MANAGER_SCOPES,  is_new=False, version_id=1),
            ]:
                db.add(ucr)

            await db.commit()
            log.info("=" * 50)
            log.info("  SEED V6 COMPLETADO EXITOSAMENTE")
            log.info("=" * 50)

        except Exception as e:
            await db.rollback()
            log.exception(f"SEED FALLO: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
