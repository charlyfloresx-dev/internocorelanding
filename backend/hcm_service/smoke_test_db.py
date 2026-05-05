import asyncio
import uuid
from datetime import date, timedelta
from hcm_app.core.database import AsyncSessionLocal
from hcm_app.models.collaborator import Collaborator

async def smoke_test_insert():
    print("🚀 Running Smoke Test DB Insertion...")
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # Test Collaborator 1: ELEGIBLE
            c1 = Collaborator(
                id=uuid.uuid4(),
                company_id=uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"), # Logistics MX
                tenant_id=uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"),
                internal_id="SMOKE-01",
                first_name="Test",
                last_name="Elegible",
                is_active=True,
                driver_license_expiry=date.today() + timedelta(days=30),
                medical_certificate_expiry=date.today() + timedelta(days=30),
                visa_expiry=date.today() + timedelta(days=30),
                rfc="GOMC801010HMN",
                curp="GOMC801010HMNRRS01"
            )
            
            # Test Collaborator 2: INELEGIBLE (Visa expiring in 5 days)
            c2 = Collaborator(
                id=uuid.uuid4(),
                company_id=uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"),
                tenant_id=uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242"),
                internal_id="SMOKE-02",
                first_name="Test",
                last_name="Expiring",
                is_active=True,
                driver_license_expiry=date.today() + timedelta(days=30),
                medical_certificate_expiry=date.today() + timedelta(days=30),
                visa_expiry=date.today() + timedelta(days=5), # TRIGGER
                rfc="GOMC801010HMX",
                curp="GOMC801010HMNRRS02"
            )

            db.add(c1)
            db.add(c2)
            print("✅ Smoke test collaborators added to db.")

if __name__ == "__main__":
    asyncio.run(smoke_test_insert())
