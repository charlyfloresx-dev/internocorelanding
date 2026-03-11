import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal

# Add backend to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Models from Auth Service
from auth_service.app.models.user import User
from auth_service.app.models.role import Role
from auth_service.app.models.permission import Permission
from auth_service.app.models.user_company_role import UserCompanyRole
from common.models.company import Company # Use the unified one

# Models from Master Data
from master_data_service.app.models.product import Product, ProductVersion, ProductType, ProductStatus, VersionStatus
from master_data_service.app.models.category import ProductCategory
from master_data_service.app.models.uom import UOM

# Models from WMS
from wms_service.app.models.warehouse import Warehouse
from wms_service.app.models.concept import Concept, ConceptType
from wms_service.app.models.inventory_snapshot import InventorySnapshot
from wms_service.app.models.inventory_document import InventoryDocument, DocumentStatus

# Models from Subscription
from subscription_service.app.models.subscription import Subscription, Plan, Entitlement
from subscription_service.app.core.enums import SubscriptionStatus, ModuleCode

# Security
from auth_service.app.core.security import get_password_hash

# Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname")

# Context
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
USER_ID_DEMO = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
COMPANY_A_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
COMPANY_B_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

async def seed_demo():
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        print("🚀 Starting Refactored Demo Seeding...")

        # 1. Permisos Atómicos (Globales)
        permissions_data = [
            {"slug": "auth.user.create", "name": "Crear Usuarios", "module_name": "AUTH"},
            {"slug": "auth.user.delete", "name": "Eliminar Usuarios", "module_name": "AUTH"},
            {"slug": "wms.inventory.adjust", "name": "Ajustar Inventario", "module_name": "WMS"},
            {"slug": "wms.warehouse.manage", "name": "Gestionar Almacenes", "module_name": "WMS"},
            {"slug": "master.product.edit", "name": "Editar Productos", "module_name": "MASTER_DATA"},
        ]
        
        db_permissions = {}
        for p_data in permissions_data:
            stmt = select(Permission).where(Permission.slug == p_data["slug"])
            res = await session.execute(stmt)
            perm = res.scalar_one_or_none()
            if not perm:
                perm = Permission(
                    **p_data,
                    company_id=None, # Global
                    created_by=SYSTEM_USER_ID
                )
                session.add(perm)
            db_permissions[p_data["slug"]] = perm
        
        await session.flush()

        # 2. Roles Maestros (Globales)
        roles_data = [
            {"name": "ADMIN", "is_system_role": True, "permissions": list(db_permissions.keys())},
            {"name": "OPERATOR", "is_system_role": True, "permissions": ["wms.inventory.adjust", "master.product.edit"]},
        ]

        db_roles = {}
        for r_data in roles_data:
            stmt = select(Role).where(sa.and_(Role.name == r_data["name"], Role.company_id == None))
            res = await session.execute(stmt)
            role = res.scalar_one_or_none()
            if not role:
                role = Role(
                    name=r_data["name"],
                    is_system_role=r_data["is_system_role"],
                    company_id=None,
                    created_by=SYSTEM_USER_ID
                )
                session.add(role)
                await session.flush()
                
                # Asignar Permisos al Rol
                for p_slug in r_data["permissions"]:
                    rp = RolePermission(
                        role_id=role.id,
                        permission_id=db_permissions[p_slug].id,
                        created_by=SYSTEM_USER_ID
                    )
                    session.add(rp)
            db_roles[r_data["name"]] = role

        await session.flush()

        # 3. Cluster / Tenant Hierarchy (Usando UUIDs de json_responses.json)
        cluster_id = uuid.uuid4()
        
        existing_comp = await session.execute(select(Company).filter_by(id=COMPANY_A_ID))
        company_a = existing_comp.scalar_one_or_none()
        if not company_a:
            company_a = Company(
                id=COMPANY_A_ID,
                name="InternoCorp Enterprise",
                tax_id="TAX-A-123",
                domain="internocorp.com",
                parent_group_id=cluster_id,
                status="ACTIVE",
                created_by=SYSTEM_USER_ID
            )
            session.add(company_a)
        
        existing_comp_b = await session.execute(select(Company).filter_by(id=COMPANY_B_ID))
        company_b = existing_comp_b.scalar_one_or_none()
        if not company_b:
            company_b = Company(
                id=COMPANY_B_ID,
                name="Interno Logistics",
                tax_id="TAX-B-456",
                domain="logistics.interno",
                parent_group_id=cluster_id,
                status="ACTIVE",
                created_by=SYSTEM_USER_ID
            )
            session.add(company_b)
        
        await session.flush()

        # 4. Demo User (Charly)
        stmt_user = select(User).where(User.id == USER_ID_DEMO)
        res_user = await session.execute(stmt_user)
        demo_user = res_user.scalar_one_or_none()
        if not demo_user:
            demo_user = User(
                id=USER_ID_DEMO,
                email="admin@interno.com",
                hashed_password=get_password_hash("Dell2024"),
                company_id=company_a.id,
                is_active=True,
                created_by=SYSTEM_USER_ID
            )
            session.add(demo_user)
        await session.flush()

        # 5. User Roles Assignments
        # Charly is ADMIN in Company A
        ucr_admin_stmt = select(UserCompanyRole).where(
            sa.and_(UserCompanyRole.user_id == demo_user.id, UserCompanyRole.company_id == company_a.id)
        )
        if not (await session.execute(ucr_admin_stmt)).scalar_one_or_none():
            session.add(UserCompanyRole(
                user_id=demo_user.id,
                company_id=company_a.id,
                role_id=db_roles["ADMIN"].id,
                scopes=["*"],
                created_by=SYSTEM_USER_ID
            ))

        # Charly is OPERATOR in Company B
        ucr_op_stmt = select(UserCompanyRole).where(
            sa.and_(UserCompanyRole.user_id == demo_user.id, UserCompanyRole.company_id == company_b.id)
        )
        if not (await session.execute(ucr_op_stmt)).scalar_one_or_none():
            session.add(UserCompanyRole(
                user_id=demo_user.id,
                company_id=company_b.id,
                role_id=db_roles["OPERATOR"].id,
                scopes=["inventory:read"],
                created_by=SYSTEM_USER_ID
            ))

        # 6. Master Data & Subscription (Simplificado para brevedad, manteniendo lógica anterior)
        # Activar todos los módulos para las compañías de demo
        for cid in [company_a.id, company_b.id]:
            # Plan Pro
            plan_stmt = select(Plan).where(Plan.name == "Plan Pro Refactor")
            plan_res = await session.execute(plan_stmt)
            plan_pro = plan_res.scalar_one_or_none()
            if not plan_pro:
                plan_pro = Plan(
                    name="Plan Pro Refactor",
                    description="Acceso total",
                    price=0.0,
                    modules=[m.value for m in ModuleCode],
                    version_id=1,
                    created_by=SYSTEM_USER_ID
                )
                session.add(plan_pro)
                await session.flush()

            # Suscripción
            sub_stmt = select(Subscription).where(Subscription.company_id == cid)
            if not (await session.execute(sub_stmt)).scalar_one_or_none():
                sub = Subscription(
                    company_id=cid,
                    plan_id=plan_pro.id,
                    status=SubscriptionStatus.ACTIVE,
                    start_date=datetime.now(timezone.utc),
                    version_id=1,
                    created_by=SYSTEM_USER_ID
                )
                session.add(sub)
                await session.flush()

                for m_code in ModuleCode:
                    session.add(Entitlement(
                        company_id=cid,
                        module_code=m_code,
                        is_enabled=True,
                        source_subscription_id=sub.id,
                        version_id=1,
                        created_by=SYSTEM_USER_ID
                    ))

        # 7. MES Industrial Categories (Phase 17.5)
        # Import dynamically to avoid circular dependencies if any, though here it's a script
        try:
            from mes_service.scripts.seed_mes_industrial import seed_mes_industrial
            await seed_mes_industrial()
            print("📅 MES Industrial Categories Seeded.")
        except ImportError:
            print("⚠️ Could not import seed_mes_industrial. Skipping.")

        await session.commit()
        print("🎉 Refactored Demo Seeding Completed!")

if __name__ == "__main__":
    asyncio.run(seed_demo())
