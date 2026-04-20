import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def verify():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT folio, company_id, destination_company_id, status 
            FROM inter_company_transfers 
            WHERE folio = 'ICT-TEST-50'
        """))
        row = res.fetchone()
        if row:
            print("-" * 50)
            print(f"✅ ENCONTRADO!")
            print(f"Folio:      {row[0]}")
            print(f"Empresa A:  {row[1]} (Enterprise)")
            print(f"Empresa B:  {row[2]} (Logistics MX)")
            print(f"Estado:     {row[3]}")
            print("-" * 50)
        else:
            print("❌ FOLIO NO ENCONTRADO EN LA DB")

if __name__ == "__main__":
    asyncio.run(verify())
