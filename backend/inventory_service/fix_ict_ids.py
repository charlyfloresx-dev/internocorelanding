import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def fix():
    enterprise_id = "9cd9986b-89da-48b7-8733-26a2a1225b01"
    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            UPDATE inter_company_transfers 
            SET company_id = :ent, tenant_id = :ent
            WHERE folio = 'ICT-TEST-50'
        """), {"ent": enterprise_id})
        await db.commit()
        print("✅ Registro ICT-TEST-50 actualizado con IDs de Enterprise.")

if __name__ == "__main__":
    asyncio.run(fix())
