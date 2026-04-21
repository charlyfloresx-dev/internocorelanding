import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.config import settings

from master_app.models.location import InventoryLocation
from master_app.models.warehouse import Warehouse
from auth_app.models.user import User
from auth_app.models.role import Role
from auth_app.models.user_company_role import UserCompanyRole
from auth_app.models.company import Company

async def setup_audit_scenario():
    print("🛠️  Detectando Entorno para Prueba de Fuego...")
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # 1. Detectar Empresa Real
        res_comp = await session.execute(select(Company).limit(1))
        company = res_comp.scalar_one_or_none()
        if not company:
            print("❌ Error: No hay empresas en la DB. Abortando.")
            return
        
        company_id = company.id
        tenant_id = company_id
        print(f"🏢 Empresa detectada: {company.name} ({company_id})")

        # 2. Asegurar el Rol
        res_role = await session.execute(select(Role).where(Role.name == "OPERATIONS_MANAGER"))
        role = res_role.scalar_one_or_none()
        if not role:
            role = Role(id=uuid.uuid4(), name="OPERATIONS_MANAGER", is_system_role=True, tenant_id=tenant_id)
            session.add(role)
            await session.flush()
        print(f"✅ Rol OPERATIONS_MANAGER listo.")

        # 3. Configurar Ubicación LOC-AUDIT-01
        res_wh = await session.execute(select(Warehouse).where(Warehouse.company_id == company_id))
        warehouse = res_wh.scalars().first()
        if warehouse:
            res_loc = await session.execute(select(InventoryLocation).where(InventoryLocation.code == "LOC-AUDIT-01"))
            loc = res_loc.scalar_one_or_none()
            if not loc:
                loc = InventoryLocation(
                    id=uuid.uuid4(), code="LOC-AUDIT-01", warehouse_id=warehouse.id,
                    company_id=company_id, tenant_id=tenant_id, capacity_m3=100.0, is_active=True
                )
                session.add(loc)
            else:
                loc.capacity_m3 = 100.0
            print(f"✅ Ubicación LOC-AUDIT-01 configurada en {warehouse.name} (Capacidad: 100).")

        # 4. Asignar rol a usuarios
        res_users = await session.execute(select(User))
        users = res_users.scalars().all()
        for u in users:
            res_assoc = await session.execute(select(UserCompanyRole).where(UserCompanyRole.user_id == u.id, UserCompanyRole.role_id == role.id, UserCompanyRole.company_id == company_id))
            if not res_assoc.scalar_one_or_none():
                session.add(UserCompanyRole(id=uuid.uuid4(), user_id=u.id, company_id=company_id, role_id=role.id, tenant_id=tenant_id))
        
        await session.commit()
        print("🚀 Escenario Listo. Datos reales vinculados.")

if __name__ == "__main__":
    asyncio.run(setup_audit_scenario())
