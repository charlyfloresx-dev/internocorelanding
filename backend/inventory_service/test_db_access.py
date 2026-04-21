import asyncio
import uuid
from sqlalchemy import text
from inventory_app.db.session import AsyncSessionLocal

async def test_access():
    folio = 'ICT-TEST-50'
    requester_id = uuid.UUID('9cd9986b-89da-48b7-8733-26a2a1225b01') # Enterprise
    
    async with AsyncSessionLocal() as db:
        # 1. Intento buscarlo sin filtros de tenant
        res = await db.execute(text("SELECT id, company_id, destination_company_id, tenant_id FROM inter_company_transfers WHERE folio = :f"), {"f": folio})
        row = res.fetchone()
        
        if not row:
            print("❌ ERROR: El folio no existe en la tabla.")
            return

        db_id, db_origin, db_dest, db_tenant = row
        print(f"✅ Registro encontrado en DB:")
        print(f"   ID:          {db_id}")
        print(f"   Origin:      {db_origin} (Type: {type(db_origin)})")
        print(f"   Dest:        {db_dest}")
        print(f"   Tenant:      {db_tenant}")
        
        # 2. Simular la validación del handler
        origin_match = str(db_origin) == str(requester_id)
        dest_match = str(db_dest) == str(requester_id)
        
        print(f"🔍 Simulación de Seguridad:")
        print(f"   Requester:   {requester_id}")
        print(f"   Match Origen: {origin_match}")
        print(f"   Match Dest:   {dest_match}")
        
        if origin_match or dest_match:
            print("🟢 ACCESO PERMITIDO (Lógica local)")
        else:
            print("🔴 ACCESO DENEGADO (Lógica local)")

if __name__ == "__main__":
    asyncio.run(test_access())
