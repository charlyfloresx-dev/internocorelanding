import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Intentamos importar dinámicamente para evitar errores de __init__
try:
    from app.models import Product, InventoryDocument, InventoryMovement, Warehouse
    from app.models.inventory import InventoryDocumentStatus
except ImportError:
    # Si falla, intentamos rutas alternativas comunes en Clean Architecture
    from app.models.product import Product
    from app.models.inventory import InventoryDocument, InventoryMovement, InventoryDocumentStatus
    from app.models.warehouse import Warehouse

from app.core.database import engine

async def test_flow():
    async with AsyncSession(engine) as session:
        # Usamos el ID de la empresa demo que ya creamos
        company_id = uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")
        
        print("🔍 Buscando Warehouse...")
        wh_res = await session.execute(select(Warehouse).limit(1))
        warehouse = wh_res.scalar_one_or_none()
        
        if not warehouse:
            print("❌ No hay almacenes. Corre primero el seed de warehouses.")
            return

        print(f"📦 Usando Almacén: {warehouse.code}")

        # Crear Producto rápido
        product = Product(
            id=uuid.uuid4(),
            company_id=company_id,
            sku=f"TEST-{uuid.uuid4().hex[:4].upper()}",
            name="Producto de Prueba",
            is_active=True
        )
        session.add(product)

        # Crear Documento
        doc = InventoryDocument(
            id=uuid.uuid4(),
            company_id=company_id,
            folio=f"T-DOC-{uuid.uuid4().hex[:4].upper()}",
            status=InventoryDocumentStatus.CONFIRMED, # Lo creamos confirmado para ver el efecto
            concept_code="ENT",
            date=datetime.now(timezone.utc)
        )
        session.add(doc)
        
        await session.commit()
        print(f"✅ Flujo completado. Producto {product.sku} y Documento {doc.folio} creados.")

if __name__ == "__main__":
    asyncio.run(test_flow())