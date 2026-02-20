import asyncio
import sys
import uuid
from sqlalchemy import text, select
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append("/app")
sys.path.append("/app/auth_service")

from app.core.database import engine
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.models.user_company_role import UserCompanyRole

# --- CONSTANTES HOMOLOGADAS ---
CO_ENTERPRISE_ID = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
CO_LOGISTICS_ID = uuid.UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")
CO_NEW_PLANT_ID = uuid.UUID("74528f80-0001-4b1e-a5b3-d2a84c1f9e12")
# ------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    print("\n🔐 [SEED AUTH] Homologando accesos...")
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Limpieza (Solo para modo demo)
            await session.execute(text("TRUNCATE TABLE user_company_roles, users, roles, companies RESTART IDENTITY CASCADE;"))

            # 1. Roles
            admin_role = Role(id=uuid.uuid4(), name="admin")
            operator_role = Role(id=uuid.uuid4(), name="operator")
            session.add_all([admin_role, operator_role])
            
            # 2. Empresas
            co1 = Company(id=CO_ENTERPRISE_ID, name="InternoCorp Enterprise")
            co2 = Company(id=CO_LOGISTICS_ID, name="Interno Logistics")
            co3 = Company(id=CO_NEW_PLANT_ID, name="Nueva Planta Demo")
            session.add_all([co1, co2, co3])
            
            # 3. Usuario Maestro
            user = User(
                id=uuid.uuid4(),
                email="admin@interno.com",
                hashed_password=pwd_context.hash("admin123456"),
                company_id=CO_ENTERPRISE_ID,
                is_active=True
            )
            session.add(user)
            await session.flush() 

            # 4. Relaciones Multi-tenant
            relaciones = [
                UserCompanyRole(
                    user_id=user.id,
                    company_id=CO_ENTERPRISE_ID,
                    role_id=admin_role.id,
                    is_new=False,
                    scopes=['catalog:admin', 'inventory:admin', 'production_mes:admin']
                ),
                UserCompanyRole(
                    user_id=user.id,
                    company_id=CO_LOGISTICS_ID,
                    role_id=operator_role.id,
                    is_new=False,
                    scopes=['inventory:read', 'inventory:execute_transfer']
                ),
                UserCompanyRole(
                    user_id=user.id,
                    company_id=CO_NEW_PLANT_ID,
                    role_id=admin_role.id,
                    is_new=True,
                    scopes=['catalog:admin', 'inventory:admin', 'production_mes:admin']
                )
            ]
            session.add_all(relaciones)
        
        await session.commit()
        print("✅ [AUTH] Homologación completada.")

if __name__ == "__main__":
    asyncio.run(seed())