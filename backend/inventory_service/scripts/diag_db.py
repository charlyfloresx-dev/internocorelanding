import asyncio
import uuid
from datetime import datetime
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def diagnose_raw_sql():
    async with AsyncSessionLocal() as session:
        # 1. Limpiar mesa
        print("[*] Lote de Diagnóstico: TRUNCATE CASCADE...")
        await session.execute(text("TRUNCATE TABLE customs_pedimentos CASCADE"))
        await session.commit()
        
        # 2. Verificar que está vacía
        result = await session.execute(text("SELECT count(*) FROM customs_pedimentos"))
        count = result.scalar()
        print(f"[!] TOTAL_PEDIMENTOS_BEFORE: {count}")

        # 3. Insertar mediante SQL PURO
        # Usaremos campos obligatorios según mi auditoría previa del modelo
        p_number = f"RAW-{uuid.uuid4().hex[:10].upper()}"
        print(f"[*] INTENTANDO INSERTAR RAW: {p_number}")
        
        company_id = "9cd9986b-89da-48b7-8733-26a2a1225b01"
        ped_id = str(uuid.uuid4())
        user_id = "69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38"
        
        insert_stmt = text("""
            INSERT INTO customs_pedimentos (
                id, company_id, tenant_id, pedimento_number, customs_key, 
                operation_type, customs_date, is_temporary, created_by, created_at
            ) VALUES (
                :id, :cid, :cid, :pnum, 'IM', 
                'IMPORT', :now, true, :uid, :now
            )
        """)
        
        try:
            await session.execute(insert_stmt, {
                "id": ped_id, "cid": company_id, "pnum": p_number, 
                "now": datetime.now(), "uid": user_id
            })
            await session.commit()
            print("✅ INSERCIÓN RAW EXITOSA!")
        except Exception as e:
            print(f"❌ FALLÓ INSERCIÓN RAW: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(diagnose_raw_sql())
