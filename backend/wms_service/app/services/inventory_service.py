import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.item import Item
from app.schemas.inventory import MasterDataSyncPayload, SyncResult

class InventoryService:
    async def sync_initial_data(
        self, db: AsyncSession, company_id: uuid.UUID, payload: MasterDataSyncPayload
    ) -> SyncResult:
        created_count = 0
        updated_count = 0
        processed_count = 0
        
        for product in payload.products:
            for version in product.versions:
                processed_count += 1
                # Buscar si ya existe el item localmente por SKU y VERSIÓN
                stmt = select(Item).where(
                    Item.company_id == company_id,
                    Item.sku == product.sku,
                    Item.version_number == version.version_number
                )
                result = await db.execute(stmt)
                item = result.scalar_one_or_none()

                if item:
                    # Actualizar datos que pueden cambiar, como el nombre
                    item.name = product.name
                    # master_product_id no debería cambiar si el SKU es el mismo, pero lo aseguramos
                    item.master_product_id = product.id
                    updated_count += 1
                else:
                    # Crear un nuevo registro de Item para esta versión
                    item = Item(
                        company_id=company_id,
                        master_product_id=product.id,
                        sku=product.sku,
                        name=product.name,
                        version_number=version.version_number,
                        stock_quantity=0.0 # Inicializar en 0
                    )
                    db.add(item)
                    created_count += 1
        
        await db.commit()
        return SyncResult(processed=processed_count, created=created_count, updated=updated_count)