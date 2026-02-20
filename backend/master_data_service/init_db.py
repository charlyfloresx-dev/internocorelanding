import asyncio
import uuid
import sys
import os

# 1. Asegurar que Python encuentre 'common' y 'app'
sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.session import engine

# Intentar importar enums desde common
try:
    from common.enums import ProductStatus, VersionStatus, ProductType
except ImportError:
    # Fallback por si acaso tus enums están en otra subcarpeta de common
    from common.models.enums import ProductStatus, VersionStatus, ProductType

# --- IDs HOMOLOGADOS ---
CO_ENTERPRISE_ID = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
UM_UNIDAD_ID = uuid.UUID("c2b3d4e5-f6a7-4b5c-8d9e-0f1a2b3c4d5e")
CAT_ELECTRONICS_ID = uuid.UUID("d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a")
PROD_IPHONE_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

async def seed_master():
    print("\n📦 [SEED MASTER DATA] Iniciando carga de datos maestros...")
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    SEED_USER_ID = uuid.uuid4() # Auditoría con UUID real para cumplir con AuditBase
    print(f"👤 Auditoría: Las operaciones se registrarán con el User ID: '{SEED_USER_ID}'.")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Limpieza total (RESTART IDENTITY para empezar de cero)
            
            print("🧹 Limpiando tablas...")
            print("🧹 Limpiando tablas...")
            await session.execute(text("""
                TRUNCATE TABLE product_versions, products, product_categories, ums
                RESTART IDENTITY CASCADE;
            """))

            # 2. Insertar UM
            print("🔢 Creando UMs...")
            await session.execute(text("""
                INSERT INTO ums (id, name, code, conversion_factor, company_id, created_at, created_by, is_active, version_id)
                VALUES (:id, 'Unidad', 'UN', 1.0, :co_id, now(), :user_id, true, 1)
            """), {
                "id": UM_UNIDAD_ID, "co_id": CO_ENTERPRISE_ID, "user_id": SEED_USER_ID
            })

            # 3. Insertar Categoría
            print("📁 Creando Categorías...")
            await session.execute(text("""
                INSERT INTO product_categories (id, name, description, company_id, created_at, created_by, is_active, version_id)
                VALUES (:id, 'Electrónica', 'Gadgets y tecnología', :co_id, now(), :user_id, true, 1)
            """), {
                "id": CAT_ELECTRONICS_ID, "co_id": CO_ENTERPRISE_ID, "user_id": SEED_USER_ID
            })

            # 4. Insertar Producto
            print("📱 Creando Productos...")
            await session.execute(text("""
                INSERT INTO products (id, sku, name, product_type, status, category_id, company_id, created_at, created_by, is_active, version_id)
                VALUES (:id, 'IPH-15-PRO', 'iPhone 15 Pro', :p_type, :status, :cat_id, :co_id, now(), :user_id, true, 1)
            """), {
                "id": PROD_IPHONE_ID, 
                "p_type": ProductType.GOODS.value,       # Corregido: FINAL_PRODUCT -> GOODS
                "status": ProductStatus.ACTIVE.value, 
                "cat_id": CAT_ELECTRONICS_ID, 
                "co_id": CO_ENTERPRISE_ID,
                "user_id": SEED_USER_ID
            })

            # 5. Insertar Versión
            print("⚙️ Creando Versiones de Producto...")
            await session.execute(text("""
                INSERT INTO product_versions (id, product_id, version_number, version_status, um_id, is_active, is_validated, company_id, created_at, created_by, version_id)
                VALUES (:id, :p_id, 1, :v_status, :um_id, true, true, :co_id, now(), :user_id, 1)
            """), {
                "id": uuid.uuid4(), 
                "p_id": PROD_IPHONE_ID, 
                "v_status": VersionStatus.PUBLISHED.value, # Corregido: RELEASED -> PUBLISHED
                "um_id": UM_UNIDAD_ID, 
                "co_id": CO_ENTERPRISE_ID,
                "user_id": SEED_USER_ID
            })

            await session.commit()
            print("\n✅ [MASTER DATA] Seed completado con éxito.")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error crítico en seed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_master())