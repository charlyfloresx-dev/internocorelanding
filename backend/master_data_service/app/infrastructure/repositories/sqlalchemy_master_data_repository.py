import uuid
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.domain.repositories.master_data_repository import IMasterDataRepository
from app.models.product import Product, ProductVersion
from app.models.product_brand import ProductBrand
from app.models.product_category import ProductCategory
from app.models.uom import UOM
from common.domain import ProductStatus, VersionStatus


class SQLAlchemyMasterDataRepository(IMasterDataRepository):
    """Concrete SQLAlchemy implementation of IMasterDataRepository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Product
    # =========================================================================
    async def get_products(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        filters = [Product.company_id == company_id]
        if group_id:
            filters = [or_(Product.company_id == company_id, Product.group_id == group_id)]
        stmt = select(Product).where(*filters)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_product_by_id(self, product_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        stmt = select(Product).where(Product.id == product_id, Product.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_product(self, product_data: dict, version_data: dict) -> Any:
        try:
            async with self.db.begin():
                new_product = Product(**product_data)
                self.db.add(new_product)
                await self.db.flush()

                version_data["product_id"] = new_product.id
                initial_ver = ProductVersion(**version_data)
                self.db.add(initial_ver)

            await self.db.refresh(new_product)
            return new_product
        except IntegrityError as e:
            if "sku" in str(e.orig):
                from common.exceptions import BusinessRuleException
                raise BusinessRuleException(f"El SKU '{product_data.get('sku')}' ya existe en esta compania.")
            raise e

    async def approve_version(self, product_id: uuid.UUID, version_number: int, company_id: uuid.UUID) -> Any:
        stmt = select(ProductVersion).where(
            ProductVersion.product_id == product_id,
            ProductVersion.version_number == version_number,
            ProductVersion.company_id == company_id
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            return None

        await self.db.execute(
            update(ProductVersion)
            .where(ProductVersion.product_id == product_id, ProductVersion.company_id == company_id)
            .values(is_active=False)
        )
        version.version_status = VersionStatus.PRODUCTION
        version.is_active = True
        version.is_validated = True
        await self.db.commit()
        return version

    # =========================================================================
    # Brand
    # =========================================================================
    async def get_brands(self, company_id: uuid.UUID) -> List[Any]:
        stmt = select(ProductBrand).where(
            or_(ProductBrand.company_id == None, ProductBrand.company_id == company_id)
        ).order_by(ProductBrand.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_brand_by_id(self, brand_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        stmt = select(ProductBrand).where(
            ProductBrand.id == brand_id,
            or_(ProductBrand.company_id == None, ProductBrand.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_brand(self, brand_data: dict, company_id: uuid.UUID) -> Any:
        db_obj = ProductBrand(company_id=company_id, **brand_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_brand(self, brand_id: uuid.UUID, update_data: dict) -> Any:
        stmt = select(ProductBrand).where(ProductBrand.id == brand_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete_brand(self, brand_id: uuid.UUID) -> None:
        stmt = select(ProductBrand).where(ProductBrand.id == brand_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()

    # =========================================================================
    # Category
    # =========================================================================
    async def get_categories(self, company_id: uuid.UUID) -> List[Any]:
        stmt = select(ProductCategory).where(
            or_(ProductCategory.company_id == None, ProductCategory.company_id == company_id)
        ).order_by(ProductCategory.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_category_by_id(self, category_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        stmt = select(ProductCategory).where(
            ProductCategory.id == category_id,
            or_(ProductCategory.company_id == None, ProductCategory.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_category(self, category_data: dict, company_id: uuid.UUID) -> Any:
        db_obj = ProductCategory(company_id=company_id, **category_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_category(self, category_id: uuid.UUID, update_data: dict) -> Any:
        stmt = select(ProductCategory).where(ProductCategory.id == category_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete_category(self, category_id: uuid.UUID) -> None:
        stmt = select(ProductCategory).where(ProductCategory.id == category_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()

    # =========================================================================
    # UOM
    # =========================================================================
    async def get_uoms(self, company_id: uuid.UUID) -> List[Any]:
        stmt = select(UOM).where(
            or_(UOM.company_id == None, UOM.company_id == company_id)
        ).order_by(UOM.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_uom_by_id(self, uom_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        stmt = select(UOM).where(
            UOM.id == uom_id,
            or_(UOM.company_id == None, UOM.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_uom(self, uom_data: dict, company_id: uuid.UUID) -> Any:
        db_obj = UOM(company_id=company_id, **uom_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    # =========================================================================
    # Sync
    # =========================================================================
    async def get_all_master_data(self, company_id: uuid.UUID) -> dict:
        stmt_products = (
            select(Product)
            .where(Product.company_id == company_id)
            .options(selectinload(Product.versions))
        )
        products_result = await self.db.execute(stmt_products)
        products = products_result.scalars().all()

        stmt_uoms = select(UOM).where(UOM.company_id == company_id)
        uoms_result = await self.db.execute(stmt_uoms)
        uoms = uoms_result.scalars().all()

        return {"products": products, "uoms": uoms}
