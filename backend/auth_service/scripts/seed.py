import os
import sys
import asyncio
import logging
import uuid
from dotenv import load_dotenv

# 1. Path Normalization
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICE_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
if SERVICE_APP not in sys.path:
    sys.path.insert(0, SERVICE_APP)

os.chdir(SERVICE_APP) 
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. Environment Setup
load_dotenv()
db_url = os.getenv('INT_DATABASE_URL') or os.getenv('DATABASE_URL') or "postgresql+asyncpg://user:password@localhost:5433/dbname"
logger.info(f"Using Database URL: {db_url}")

# 3. App Imports - Use ONLY app.models and avoid common.models to prevent registry conflicts
from app.core.database import AsyncSessionLocal
from app.models import BusinessGroup, Company, User, Role, UserCompanyRole
from app.core.security import hash_password
from sqlalchemy import select

async def run_seed():
    logger.info("🌱 Iniciando seeding del Auth Service (RFID & Multi-Tenant Support)...")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Crear Business Group (Cluster)
            group_id = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
            group_name = "InternoCorp Group"
            stmt = select(BusinessGroup).where(BusinessGroup.id == group_id)
            res = await db.execute(stmt)
            corp_group = res.scalar_one_or_none()
            
            if not corp_group:
                corp_group = BusinessGroup(
                    id=group_id,
                    name=group_name,
                    description="Cluster de manufactura principal"
                )
                db.add(corp_group)
                await db.flush()
                logger.info(f"✅ Business Group '{group_name}' creado.")

            # 2. Definir Empresas del Cluster
            companies_data = [
                {
                    "id": uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01"),
                    "name": "InternoCorp Enterprise",
                    "group_id": group_id,
                    "is_new": False
                },
                {
                    "id": uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"),
                    "name": "Interno Logistics (Tijuana Plant)",
                    "group_id": group_id,
                    "is_new": False
                },
                {
                    "id": uuid.UUID("203e03c9-5d65-43ff-9e83-864ef605426c"),
                    "name": "Nueva Planta Demo",
                    "group_id": group_id,
                    "is_new": True
                }
            ]
            
            seeded_companies = []
            for c_data in companies_data:
                stmt = select(Company).where(Company.id == c_data["id"])
                res = await db.execute(stmt)
                company = res.scalar_one_or_none()
                
                if not company:
                    company = Company(
                        id=c_data["id"],
                        name=c_data["name"],
                        parent_group_id=c_data["group_id"],
                        status="ACTIVE",
                        version_id=1,
                        is_active=True
                    )
                    db.add(company)
                    await db.flush()
                    logger.info(f"✅ Empresa '{c_data['name']}' creada.")
                else:
                    logger.info(f"ℹ️ Empresa '{c_data['name']}' ya existe.")
                seeded_companies.append((company, c_data["is_new"]))

            # 3. Crear Roles Estándar
            roles_to_create = ["admin", "owner", "supervisor", "member", "operator"]
            for company, _ in seeded_companies:
                for r_name in roles_to_create:
                    stmt = select(Role).where(Role.name == r_name, Role.company_id == company.id)
                    res = await db.execute(stmt)
                    if not res.scalar_one_or_none():
                        role = Role(
                            name=r_name,
                            company_id=company.id,
                            version_id=1,
                            is_active=True
                        )
                        db.add(role)
                await db.flush()
            logger.info("✅ Roles de base creados.")

            # 4. Crear Usuarios (Admin Charly y Operador RFID)
            users_to_seed = [
                {
                    "id": uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38"),
                    "email": "charly@interno.com",
                    "password": "charly123",
                    "identity_token": None,
                    "companies": [seeded_companies[0][0], seeded_companies[1][0]], # Acceso a 2 empresas
                    "role_name": "admin"
                },
                {
                    "id": uuid.UUID("d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a"),
                    "email": "op01@interno.com",
                    "password": "operator123",
                    "identity_token": "RFID123456",
                    "companies": [seeded_companies[1][0]], # Acceso a Tijuana
                    "role_name": "operator"
                }
            ]

            for u_data in users_to_seed:
                stmt = select(User).where(User.email == u_data["email"])
                res = await db.execute(stmt)
                user = res.scalar_one_or_none()
                
                if not user:
                    user = User(
                        id=u_data["id"],
                        email=u_data["email"],
                        hashed_password=hash_password(u_data["password"]),
                        identity_token=u_data["identity_token"],
                        company_id=u_data["companies"][0].id,
                        version_id=1,
                        is_active=True
                    )
                    db.add(user)
                    await db.flush()
                    logger.info(f"✅ Usuario {u_data['email']} creado (RFID: {u_data['identity_token']}).")
                
                # Vincular a empresas
                for company in u_data["companies"]:
                    r_stmt = select(Role).where(Role.name == u_data["role_name"], Role.company_id == company.id)
                    r_res = await db.execute(r_stmt)
                    target_role = r_res.scalar_one()

                    link_stmt = select(UserCompanyRole).where(
                        UserCompanyRole.user_id == user.id,
                        UserCompanyRole.company_id == company.id
                    )
                    link_res = await db.execute(link_stmt)
                    if not link_res.scalar_one_or_none():
                        link = UserCompanyRole(
                            user_id=user.id,
                            company_id=company.id,
                            role_id=target_role.id,
                            is_new=False,
                            version_id=1
                        )
                        db.add(link)
                        logger.info(f"🔗 Vinculando {u_data['email']} a '{company.name}' como {u_data['role_name']}.")

            await db.commit()
            logger.info("🚀 Seeding Seed v3.0 (RFID & Multi-Tenant) completado.")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error en seed: {e}")
            raise
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(run_seed())