import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.item_repository import IItemRepository
from app.domain.entities.item import ItemEntity
from app.models.item import Item

class SQLAlchemyItemRepository(IItemRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: Item) -> ItemEntity:
        return ItemEntity(
            id=model.id,
            company_id=model.company_id,
            code=model.code,
            name=model.name,
            sku=model.sku,
            version_number=model.version_number,
            stock_quantity=model.stock_quantity,
            master_product_id=model.master_product_id
        )

    async def get_by_sku(self, company_id: uuid.UUID, sku: str, version_number: int) -> Optional[ItemEntity]:
        stmt = select(Item).where(
            Item.company_id == company_id,
            Item.sku == sku,
            Item.version_number == version_number
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: ItemEntity) -> None:
        stmt = select(Item).where(Item.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            model = Item(
                id=entity.id,
                company_id=entity.company_id,
                code=entity.code,
                name=entity.name,
                sku=entity.sku,
                version_number=entity.version_number,
                stock_quantity=entity.stock_quantity,
                master_product_id=entity.master_product_id
            )
            self.session.add(model)
        else:
            model.name = entity.name
            model.stock_quantity = entity.stock_quantity
            model.master_product_id = entity.master_product_id
            
        await self.session.flush()
