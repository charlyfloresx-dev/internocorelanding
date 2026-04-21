# pyre-ignore-all-errors[21]
import uuid
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, update, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from master_app.domain.repositories.master_data_repository import IMasterDataRepository
from master_app.models.product import Product, ProductVersion
from master_app.models.product_brand import ProductBrand
from master_app.models.product_category import ProductCategory
from master_app.models.uom import UOM
from common.domain import ProductStatus, VersionStatus
from master_app.models.product_price import ProductPrice
from datetime import datetime, timezone


class SQLAlchemyMasterDataRepository(IMasterDataRepository):
    """Concrete SQLAlchemy implementation of IMasterDataRepository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Product
    # =========================================================================
    async def get_products(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None, q: Optional[str] = None, warehouse_id: Optional[uuid.UUID] = None) -> List[Any]:
        filters = [Product.company_id == company_id]
        if group_id:
            filters = [or_(Product.company_id == company_id, Product.group_id == group_id)]
        
        # Resolve price list (Default 1 for now)
        # Búsqueda jerárquica: Almacén específico OR Global (NULL warehouse)
        price_warehouse_filter = or_(ProductPrice.warehouse_id == warehouse_id, ProductPrice.warehouse_id == None) if warehouse_id else ProductPrice.warehouse_id == None

        # Optimized query to fetch products with their latest price if available
        # we favor the warehouse-specific price over global via ordering or logic in join
        stmt = (
            select(Product)
            .where(*filters)
            .outerjoin(ProductPrice, and_(
                ProductPrice.product_id == Product.id,
                ProductPrice.valid_until == None,
                ProductPrice.is_active == True,
                price_warehouse_filter
            ))
            .add_columns(ProductPrice._amount, ProductPrice._currency)
        )
        
        if q:
            keyword = f"%{q}%"
            stmt = stmt.where(or_(
                Product.sku.ilike(keyword),
                Product.name.ilike(keyword)
            ))
            
        # If warehouse_id was provided, we might have 2 prices (global and local)
        # We want the local one to be processed first or selected.
        if warehouse_id:
            stmt = stmt.order_by(Product.id, ProductPrice.warehouse_id.desc().nullslast())

        result = await self.db.execute(stmt)
        
        products = []
        processed_ids = set()
        
        for row in result.all():
            p = row[0]
            if p.id in processed_ids:
                continue # Already got the best price (warehouse specific) due to order_by
                
            p.last_price = float(row[1]) if row[1] is not None else None
            p.currency = row[2] or "MXN"
            products.append(p)
            processed_ids.add(p.id)
            
        return products

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
                raise BusinessRuleException(f"SKU '{product_data.get('sku')}' already exists for this company.")
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

    async def update_product(self, product_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        stmt = select(Product).where(Product.id == product_id, Product.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            try:
                for field, value in update_data.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
                self.db.add(db_obj)
                await self.db.commit()
                await self.db.refresh(db_obj)
            except IntegrityError:
                from common.exceptions import ConflictException
                raise ConflictException(f"Update failed. Possible SKU conflict.")
        return db_obj

    async def delete_product(self, product_id: uuid.UUID, company_id: uuid.UUID) -> None:
        """Soft-delete product."""
        stmt = select(Product).where(Product.id == product_id, Product.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            db_obj.is_active = False
            self.db.add(db_obj)
            await self.db.commit()

    # =========================================================================
    # Brand
    # =========================================================================
    async def get_brands(self, company_id: uuid.UUID) -> List[Any]:
        global_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        stmt = select(ProductBrand).where(
            or_(ProductBrand.company_id == None, 
                ProductBrand.company_id == company_id,
                ProductBrand.company_id == global_id)
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
        try:
            db_obj = ProductBrand(company_id=company_id, **brand_data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            from common.exceptions import ConflictException
            raise ConflictException(f"Brand code or name already exists.")

    async def update_brand(self, brand_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        stmt = select(ProductBrand).where(ProductBrand.id == brand_id, ProductBrand.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete_brand(self, brand_id: uuid.UUID, company_id: uuid.UUID) -> None:
        stmt = select(ProductBrand).where(ProductBrand.id == brand_id, ProductBrand.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()

    # =========================================================================
    # Category
    # =========================================================================
    async def get_categories(self, company_id: uuid.UUID) -> List[Any]:
        global_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        stmt = select(ProductCategory).where(
            or_(ProductCategory.company_id == None, 
                ProductCategory.company_id == company_id,
                ProductCategory.company_id == global_id)
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
        try:
            db_obj = ProductCategory(company_id=company_id, **category_data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            from common.exceptions import ConflictException
            raise ConflictException(f"Category code or name already exists.")

    async def update_category(self, category_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        stmt = select(ProductCategory).where(ProductCategory.id == category_id, ProductCategory.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete_category(self, category_id: uuid.UUID, company_id: uuid.UUID) -> None:
        stmt = select(ProductCategory).where(ProductCategory.id == category_id, ProductCategory.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()

    # =========================================================================
    # UOM
    # =========================================================================
    async def get_uoms(self, company_id: uuid.UUID) -> List[Any]:
        global_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        stmt = select(UOM).where(
            or_(UOM.company_id == None, 
                UOM.company_id == company_id,
                UOM.company_id == global_id)
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
        try:
            db_obj = UOM(company_id=company_id, **uom_data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            from common.exceptions import ConflictException
            raise ConflictException(f"UOM code or name already exists.")

    async def update_uom(self, uom_id: uuid.UUID, company_id: uuid.UUID, update_data: dict) -> Any:
        stmt = select(UOM).where(UOM.id == uom_id, UOM.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete_uom(self, uom_id: uuid.UUID, company_id: uuid.UUID) -> None:
        stmt = select(UOM).where(UOM.id == uom_id, UOM.company_id == company_id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()

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


    # =========================================================================
    # Product Price
    # =========================================================================
    async def get_product_prices(self, product_id: uuid.UUID, company_id: uuid.UUID) -> List[Any]:
        stmt = (
            select(ProductPrice)
            .where(ProductPrice.product_id == product_id, ProductPrice.company_id == company_id)
            .order_by(ProductPrice.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def upsert_product_price(self, price_data: dict, company_id: uuid.UUID) -> Any:
        """
        Implements the 'Soft Close' / Versioning strategy.
        1. Find current active price (valid_until is NULL).
        2. Mark it as 'Soft Closed' (set valid_until = now).
        3. Create new record with valid_until = NULL.
        """
        # Ensure correct company context
        price_data["company_id"] = company_id
        
        # Unique identifying keys for a "Price entry"
        product_id = price_data.get("product_id")
        price_list_index = price_data.get("price_list_index")
        unit_type = price_data.get("unit_type")
        warehouse_id = price_data.get("warehouse_id")
        currency = price_data.get("currency")
        
        # 1. Close existing active price
        stmt = select(ProductPrice).where(
            ProductPrice.company_id == company_id,
            ProductPrice.product_id == product_id,
            ProductPrice.price_list_index == price_list_index,
            ProductPrice.unit_type == unit_type,
            ProductPrice.warehouse_id == warehouse_id,
            ProductPrice._currency == currency,
            ProductPrice.valid_until == None
        )
        result = await self.db.execute(stmt)
        existing_price = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        
        if existing_price:
            existing_price.valid_until = now
            existing_price.is_active = False # Consistent with previous Turn where we confirmed is_active should be False if closed.
            self.db.add(existing_price)
        
        # 2. Create new active version
        # Map generic price data to internal structure
        internal_data = price_data.copy()
        if "value" in internal_data:
            internal_data["_amount"] = internal_data.pop("value")
        if "currency" in internal_data:
            internal_data["_currency"] = internal_data.pop("currency")
            
        new_price = ProductPrice(
            product_id=new_price_id if 'new_price_id' in locals() else internal_data.get('product_id'),
            company_id=internal_data.get('company_id'),
            group_id=internal_data.get('group_id'),
            price_list_index=internal_data.get('price_list_index', 1),
            _amount=internal_data.get('_amount'),
            _currency=internal_data.get('_currency'),
            unit_type=internal_data.get('unit_type', UnitType.SALE),
            valid_until=None,
            is_active=True
        )
        
        self.db.add(new_price)
        await self.db.commit()
        await self.db.refresh(new_price)
        
        return new_price
