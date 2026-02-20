import asyncio
import uuid
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# No dependemos de modelos complejos para evitar errores de mapeo circular
# Usamos directamente la URL de conexión interna de Docker
DATABASE_URL = "postgresql+asyncpg://user:password@postgres-db:5432/wms_db"

# --- CONSTANTES ---
# Deben coincidir con los IDs usados en Auth y Master Data
CO_ENTERPRISE_ID = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
PROD_IPHONE_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

async def seed_wms():
    print("\n📦 [SEED WMS] Insertando datos vía SQL Directo...")
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Iniciamos una transacción
            async with session.begin():
                print("🧹 Limpiando tabla items...")
                await session.execute(text("TRUNCATE TABLE items RESTART IDENTITY CASCADE;"))

                print("📝 Insertando item de prueba (iPhone 13 Pro)...")
                # Corregido: :company_id coincide con el diccionario de parámetros
                query = text("""
                    INSERT INTO items (
                        id, 
                        master_product_id, 
                        sku, 
                        name, 
                        stock_quantity, 
                        bin_location, 
                        company_id, 
                        created_at
                    )
                    VALUES (
                        :id, 
                        :master_id, 
                        :sku, 
                        :name, 
                        :qty, 
                        :bin, 
                        :company_id, 
                        NOW()
                    )
                """)
                
                await session.execute(query, {
                    "id": uuid.uuid4(),
                    "master_id": PROD_IPHONE_ID,
                    "sku": "IPHONE-13-PRO",
                    "name": "iPhone 13 Pro 256GB",
                    "qty": 100.0,
                    "bin": "A-01-01",
                    "company_id": CO_ENTERPRISE_ID
                })
                
            await session.commit()
            print("✅ [WMS] Seed completado exitosamente vía SQL.")
            
        except Exception as e:
            print(f"❌ Error durante el seed: {e}")
            await session.rollback()
        finally:
            # Cerramos la conexión al motor
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_wms())