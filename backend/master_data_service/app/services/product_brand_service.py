import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from app.models.product_brand import ProductBrand
from app.schemas.product_brand import BrandCreate, BrandUpdate

class ProductBrandService:
    @staticmethod
    async def get_brands(db: AsyncSession, *, company_id: uuid.UUID) -> List[ProductBrand]:
        # Hybrid Query: Global (None) OR Tenant Specific
        stmt = select(ProductBrand).where(
            or_(ProductBrand.company_id == None, ProductBrand.company_id == company_id)
        ).order_by(ProductBrand.name)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_brand_by_id(db: AsyncSession, *, brand_id: uuid.UUID, company_id: uuid.UUID) -> Optional[ProductBrand]:
        stmt = select(ProductBrand).where(
            ProductBrand.id == brand_id,
            or_(ProductBrand.company_id == None, ProductBrand.company_id == company_id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_brand(db: AsyncSession, *, brand_in: BrandCreate, company_id: uuid.UUID) -> ProductBrand:
        db_obj = ProductBrand(
            company_id=company_id,
            **brand_in.model_dump()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_brand(db: AsyncSession, *, db_obj: ProductBrand, brand_in: BrandUpdate) -> ProductBrand:
        update_data = brand_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def delete_brand(db: AsyncSession, *, db_obj: ProductBrand) -> None:
        await db.delete(db_obj)
        await db.commit()