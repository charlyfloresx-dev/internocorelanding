import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from app.models.product_category import ProductCategory
from app.schemas.product_category import CategoryCreate, CategoryUpdate

class ProductCategoryService:
    @staticmethod
    async def get_categories(db: AsyncSession, *, company_id: uuid.UUID) -> List[ProductCategory]:
        # Hybrid Query: Global (None) OR Tenant Specific
        stmt = select(ProductCategory).where(
            or_(ProductCategory.company_id == None, ProductCategory.company_id == company_id)
        ).order_by(ProductCategory.name)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_category_by_id(db: AsyncSession, *, category_id: uuid.UUID, company_id: uuid.UUID) -> Optional[ProductCategory]:
        # Allow fetching if it's global OR belongs to tenant
        stmt = select(ProductCategory).where(
            ProductCategory.id == category_id,
            or_(ProductCategory.company_id == None, ProductCategory.company_id == company_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_category(db: AsyncSession, *, category_in: CategoryCreate, company_id: uuid.UUID) -> ProductCategory:
        # Force assignment of company_id to prevent users from creating Global records
        db_obj = ProductCategory(
            company_id=company_id,
            **category_in.model_dump()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_category(db: AsyncSession, *, db_obj: ProductCategory, category_in: CategoryUpdate) -> ProductCategory:
        update_data = category_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def delete_category(db: AsyncSession, *, db_obj: ProductCategory) -> None:
        await db.delete(db_obj)
        await db.commit()