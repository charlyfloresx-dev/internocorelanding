import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.uom import UM
from app.schemas.sync import MasterDataSyncResponse

class SyncService:
    async def get_all_master_data(
        self, db: AsyncSession, company_id: uuid.UUID
    ) -> MasterDataSyncResponse:
        # 1. Obtener Productos
        stmt_products = (select(Product)
            .where(Product.company_id == company_id)
            .options(selectinload(Product.versions)))
        products_result = await db.execute(stmt_products)
        products = products_result.scalars().all()

        # 2. Obtener UOMs
        stmt_uoms = select(UM).where(UM.company_id == company_id)
        uoms_result = await db.execute(stmt_uoms)
        uoms = uoms_result.scalars().all()

        return MasterDataSyncResponse(products=products, uoms=uoms)