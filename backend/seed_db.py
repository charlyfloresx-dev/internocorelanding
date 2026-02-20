import asyncio
import sys
import os
import uuid
from sqlalchemy import text
from sqlalchemy.future import select

# Configuramos las rutas para que Python encuentre los módulos
sys.path.append("/app")
sys.path.append("/app/auth_service")

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# Imports según la arquitectura de Interno Core
from common.models import Base
from app.core.database import engine
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_company_role import UserCompanyRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    print("\n🌱 [SEED] Iniciando Demo Factory para Interno Core...")
    
    # 1. LIMPIEZA SEGURA
    async with engine.begin() as conn:
        print("🧹 [DB] Limpiando datos existentes...")
        tables = ["user_company_roles", "role_permissions", "users", "roles", "permissions", "companies"]
        try:
            await conn.execute(text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"))
            print("✅ Limpieza completada.")
        except Exception as e:
            print(f"⚠️ Nota: Saltando limpieza ({e})")

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            print("📝 [DATA] Creando perfiles de demostración...")
            
            # 1. ROLES
            admin_role = Role(id=uuid.uuid4(), name="admin")
            operator_role = Role(id=uuid.uuid4(), name="operator")
            session.add_all([admin_role, operator_role])
            
            # 2. EMPRESAS
            co_enterprise = Company(id=uuid.uuid4(), name="InternoCorp Enterprise", logo="https://ui-avatars.com/api/?name=IC+Enterprise")
            co_logistics = Company(id=uuid.uuid4(), name="Interno Logistics", logo="https://ui-avatars.com/api/?name=IC+Logistics")
            co_new = Company(id=uuid.uuid4(), name="Nueva Planta Demo", logo="https://ui-avatars.com/api/?name=NP")
            session.add_all([co_enterprise, co_logistics, co_new])
            
            # 3. USUARIO MAESTRO 
            # IMPORTANTE: Asignamos company_id desde el inicio para evitar NotNullViolationError
            hashed_pw = pwd_context.hash("admin123456")
            user = User(
                id=uuid.uuid4(),
                email="admin@interno.com",
                hashed_password=hashed_pw,
                company_id=co_enterprise.id, # <--- FIX: Asignamos empresa principal
                is_active=True
            )
            session.add(user)
            
            # Flush para que los IDs existan en la transacción antes de las FKs
            await session.flush() 

            # 4. VÍNCULOS MULTI-TENANT
            relaciones = [
                UserCompanyRole(user_id=user.id, company_id=co_enterprise.id, role_id=admin_role.id, is_new=False),
                UserCompanyRole(user_id=user.id, company_id=co_logistics.id, role_id=operator_role.id, is_new=False),
                UserCompanyRole(user_id=user.id, company_id=co_new.id, role_id=admin_role.id, is_new=True)
            ]
            session.add_all(relaciones)
        
        await session.commit()
        print("\n✅ [SUCCESS] Demo Factory completado con éxito para Interno Core.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())