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

# Security
from auth_service.app.core.security import get_password_hash

# Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname")

async def seed_demo():
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        print("🚀 Starting Demo Seeding...")

        # 1. Roles & Permissions
        admin_res = await session.execute(select(Role).filter_by(name="ADMIN"))
        admin_role = admin_res.scalar_one_or_none()
        if not admin_role:
            admin_role = Role(name="ADMIN")
            session.add(admin_role)
            await session.flush()

        # 2. Cluster / Tenant Hierarchy
        cluster_id = uuid.uuid4()
        
        # Check if already seeded
        existing_comp = await session.execute(select(Company).filter_by(name="Demo-Company-A"))
        if existing_comp.scalar_one_or_none():
            print("⚠️ Demo data already exists. Skipping...")
            return

        company_a = Company(
            id=uuid.uuid4(),
            name="Demo-Company-A",
            tax_id="TAX-A-123",
            domain="comp-a.demo",
            parent_group_id=cluster_id,
            status="ACTIVE"
        )
        
        company_b = Company(
            id=uuid.uuid4(),
            name="Demo-Company-B",
            tax_id="TAX-B-456",
            domain="comp-b.demo",
            parent_group_id=cluster_id,
            status="ACTIVE"
        )
        
        session.add_all([company_a, company_b])
        await session.flush()

        # 3. Demo User
        demo_user = User(
            email="demo@internocore.com",
            hashed_password=get_password_hash("demo123"),
            company_id=company_a.id,
            is_active=True
        )
        session.add(demo_user)
        await session.flush()

        for cid in [company_a.id, company_b.id]:
            session.add(UserCompanyRole(
                user_id=demo_user.id,
                company_id=cid,
                role_id=admin_role.id,
                scopes=["*"]
            ))

        # 4. Master Data
        um_unit = UOM(company_id=company_a.id, code="PZA", name="Pieza")
        session.add(um_unit)
        
        cat = ProductCategory(company_id=company_a.id, name="Electronics")
        session.add(cat)
        await session.flush()

        products = []
        for i in range(1, 6):
            p = Product(
                company_id=company_a.id,
                sku=f"SKU-DEMO-{i}",
                name=f"Demo Product {i}",
                product_type=ProductType.GOODS,
                status=ProductStatus.ACTIVE,
                category_id=cat.id
            )
            session.add(p)
            products.append(p)
        
        await session.flush()

        for p in products:
            v = ProductVersion(
                company_id=company_a.id,
                product_id=p.id,
                version_number=1,
                version_status=VersionStatus.PUBLISHED,
                is_active=True,
                is_validated=True,
                um_id=um_unit.id
            )
            session.add(v)

        # 5. WMS Data
        wh_a = Warehouse(company_id=company_a.id, code="DEMO-A", name="Demo Warehouse A")
        session.add(wh_a)
        
        concepts = [
            Concept(company_id=company_a.id, code="ENT", name="Entrada", concept_type=ConceptType.ENTRY),
            Concept(company_id=company_a.id, code="SAL", name="Salida", concept_type=ConceptType.OUTPUT),
        ]
        session.add_all(concepts)
        await session.flush()

        # Stock Initial for Company A / Product 1
        snapshot = InventorySnapshot(
            company_id=company_a.id,
            product_id=products[0].id,
            warehouse_id=wh_a.id,
            quantity_on_hand=Decimal("100.00"),
            average_cost=Decimal("50.00")
        )
        session.add(snapshot)

        await session.commit()
        print("🎉 Demo Seeding Completed!")

if __name__ == "__main__":
    asyncio.run(seed_demo())
