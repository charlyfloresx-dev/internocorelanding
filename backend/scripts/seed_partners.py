
import asyncio
import uuid
from common.infrastructure.database import AsyncSessionLocal
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'master_data_service'))
from master_app.models.partner import Partner

async def seed_partners():
    async with AsyncSessionLocal() as session:
        ENTERPRISE_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"
        
        partners = [
            Partner(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.1"),
                code="SUP-IND-01",
                name="Proveedor Industrial Nacional S.A. de C.V.",
                type="SUPPLIER",
                company_id=ENTERPRISE_ID,
                tenant_id=ENTERPRISE_ID,
                is_active=True
            ),
            Partner(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.2"),
                code="SUP-GLO-02",
                name="Global Logistics Corp",
                type="SUPPLIER",
                company_id=ENTERPRISE_ID,
                tenant_id=ENTERPRISE_ID,
                is_active=True
            ),
            Partner(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, "partner.3"),
                code="CUS-NOR-01",
                name="Cliente Mayorista Norte",
                type="CUSTOMER",
                company_id=ENTERPRISE_ID,
                tenant_id=ENTERPRISE_ID,
                is_active=True
            )
        ]
        
        session.add_all(partners)
        await session.commit()
        print("Successfully seeded 3 business partners.")

if __name__ == "__main__":
    asyncio.run(seed_partners())
