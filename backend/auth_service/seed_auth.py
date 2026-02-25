import asyncio
import sys
import uuid
from sqlalchemy import select
from datetime import datetime, timezone
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# Aseguramos los paths para los modelos y common
sys.path.append("/app")
sys.path.append("/app/auth_service")

from app.core.database import engine
from app.models.base import Base
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.models.role_permission import RolePermission
from app.models.user_company_role import UserCompanyRole
from common.models.company import Company

# --- CONSTANTES HOMOLOGADAS ---
CO_ENTERPRISE_ID = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
CO_LOGISTICS_ID = uuid.UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")
CO_NEW_PLANT_ID = uuid.UUID("74528f80-0001-4b1e-a5b3-d2a84c1f9e12")
ADMIN_ROLE_ID = uuid.UUID("dc74a8b8-795a-4564-b987-f2099c490ba8")
OPERATOR_ROLE_ID = uuid.UUID("8c3995df-e1e5-41d2-885a-9494f0975e44")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    print("\n🔐 [SEED AUTH] Iniciando homologación de accesos...")
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 1. SINCRONIZACIÓN DE ESQUEMA (DDL)
    print("🔍 Sincronizando esquema de base de datos...")
    async with engine.begin() as conn:
        if hasattr(Company, 'metadata'):
            print(f"🔍 Asegurando tabla de compañías (common)...")
            await conn.run_sync(Company.metadata.create_all)
        await conn.run_sync(Base.metadata.create_all)

    # 2. INSERCIÓN DE DATOS (DML) CON VERIFICACIÓN
    async with AsyncSessionLocal() as session:
        try:
            # --- EMPRESAS ---
            companies_to_seed = [
                {"id": CO_ENTERPRISE_ID, "name": "InternoCorp Enterprise"},
                {"id": CO_LOGISTICS_ID, "name": "Interno Logistics"},
                {"id": CO_NEW_PLANT_ID, "name": "Nueva Planta Demo"}
            ]

            for co_data in companies_to_seed:
                existing = await session.get(Company, co_data["id"])
                if not existing:
                    print(f"➕ Insertando empresa: {co_data['name']}")
                    session.add(Company(**co_data))
            
            await session.flush()

            # --- ROLES ---
            roles_to_seed = [
                {"id": ADMIN_ROLE_ID, "name": "admin"},
                {"id": OPERATOR_ROLE_ID, "name": "operator"}
            ]

            for role_data in roles_to_seed:
                existing = await session.get(Role, role_data["id"])
                if not existing:
                    print(f"➕ Insertando rol: {role_data['name']}")
                    session.add(Role(**role_data))
            
            await session.flush()

            # --- USUARIO MAESTRO ---
            stmt_user = select(User).where(User.email == "admin@interno.com")
            result_user = await session.execute(stmt_user)
            admin_user = result_user.scalar_one_or_none()

            if not admin_user:
                print("➕ Creando usuario administrador maestro...")
                admin_user = User(
                    id=uuid.uuid4(),
                    email="admin@interno.com",
                    hashed_password=pwd_context.hash("admin123456"),
                    is_active=True,
                    company_id=CO_ENTERPRISE_ID
                )
                session.add(admin_user)
                await session.flush()
            else:
                print("ℹ️ Usuario maestro ya existe.")

            # --- RELACIONES MULTI-TENANT (UserCompanyRole) ---
            rels_data = [
                {
                    "company_id": CO_ENTERPRISE_ID, 
                    "role_id": ADMIN_ROLE_ID, 
                    "is_new": False, 
                    "scopes": ['catalog:admin', 'inventory:admin', 'production_mes:admin']
                },
                {
                    "company_id": CO_LOGISTICS_ID, 
                    "role_id": OPERATOR_ROLE_ID, 
                    "is_new": False, 
                    "scopes": ['inventory:read', 'inventory:execute_transfer']
                },
                {
                    "company_id": CO_NEW_PLANT_ID, 
                    "role_id": ADMIN_ROLE_ID, 
                    "is_new": True, 
                    "scopes": ['catalog:admin', 'inventory:admin', 'production_mes:admin']
                }
            ]

            for rel_info in rels_data:
                stmt_rel = select(UserCompanyRole).where(
                    UserCompanyRole.user_id == admin_user.id,
                    UserCompanyRole.company_id == rel_info["company_id"]
                )
                res_rel = await session.execute(stmt_rel)
                if not res_rel.scalar_one_or_none():
                    print(f"🔗 Vinculando usuario a empresa {rel_info['company_id']}...")
                    new_rel = UserCompanyRole(
                        user_id=admin_user.id,
                        company_id=rel_info["company_id"],
                        role_id=rel_info["role_id"],
                        is_new=rel_info["is_new"],
                        scopes=rel_info["scopes"]
                    )
                    session.add(new_rel)

            await session.commit()
            print("✅ [AUTH] Semillas verificadas/plantadas con éxito.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ [SEED ERROR] Falló la homologación: {str(e)}")
            raise e

if __name__ == "__main__":
    asyncio.run(seed())