# pyre-ignore-all-errors[21]
import uuid
from typing import List, Optional, Any, Dict
from decimal import Decimal
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
        
        price_warehouse_filter = or_(ProductPrice.warehouse_id == warehouse_id, ProductPrice.warehouse_id == None) if warehouse_id else ProductPrice.warehouse_id == None

        from sqlalchemy import text, table, column
        # Define variant table dynamically to avoid cross-service import dependencies
        variants = table("inventory_item_variants",
            column("id"),
            column("product_id"),
            column("mfg_part_number"),
            column("brand")
        )

        stmt = (
            select(Product)
            .where(*filters)
            .outerjoin(variants, variants.c.product_id == Product.id)

            .outerjoin(ProductPrice, and_(
                ProductPrice.product_id == Product.id,
                ProductPrice.valid_until == None,
                ProductPrice.is_active == True,
                price_warehouse_filter
            ))
            .add_columns(
                ProductPrice._amount, 
                ProductPrice._currency,
                variants.c.mfg_part_number,
                variants.c.brand,
                variants.c.id.label("variant_id")
            )
        )
        
        if q:
            keyword = f"%{q}%"
            stmt = stmt.where(or_(
                Product.sku.ilike(keyword),
                Product.name.ilike(keyword),
                variants.c.mfg_part_number.ilike(keyword)
            ))

            
        if warehouse_id:
            stmt = stmt.order_by(Product.id, ProductPrice.warehouse_id.desc().nullslast())

        result = await self.db.execute(stmt)
        
        products = []
        processed_keys = set()
        
        for row in result.all():
            p_orig = row[0]
            # Create a shallow copy to avoid modifying the same object for different variants
            import copy
            p = copy.copy(p_orig)
            
            p_id = p.id
            mpn = row[3]
            brand = row[4]
            variant_id = row[5]
            
            # Key for uniqueness: Product ID + Variant ID (to show different variants)
            # We also keep the price logic
            key = (p_id, variant_id)
            if key in processed_keys:
                continue 
                
            p.last_price = Decimal(str(row[1])) if row[1] is not None else None
            p.currency = row[2] or "MXN"
            
            # Enrich Name with Variant Info if it exists
            if mpn:
                p.name = f"{p.name} ({brand} {mpn})"
                # Optionally, override SKU to be specific if MPN is what they need
                # but for inventory documents, usually SKU is the product and MPN is the variant attribute.
            
            products.append(p)
            processed_keys.add(key)
            
        return products


    async def get_product_by_id(self, product_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Any]:
        stmt = select(Product).where(Product.id == product_id, Product.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product_by_sku(self, sku: str, company_id: uuid.UUID) -> Optional[Any]:
        """
        Unifies lookup by SKU (Main Product) or MFG/Internal SKU (Variant).
        Always joins with ProductPrice to ensure 'last_price' is available.
        """
        from sqlalchemy import text, table, column
        variants = table("inventory_item_variants",
            column("id"),
            column("product_id"),
            column("internal_sku"),
            column("mfg_part_number"),
            column("brand"),
            column("unit_price")
        )

        # Base statement with Price Join and Variant info
        stmt = (
            select(Product)
            .outerjoin(variants, variants.c.product_id == Product.id)
            .outerjoin(ProductPrice, and_(
                ProductPrice.product_id == Product.id,
                ProductPrice.valid_until == None,
                ProductPrice.is_active == True
            ))
            .outerjoin(ProductBrand, Product.brand_id == ProductBrand.id)
            .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
            .outerjoin(UOM, Product.base_uom_id == UOM.id)
            .where(Product.company_id == company_id)
            .add_columns(
                ProductPrice._amount,
                ProductPrice._currency,
                variants.c.mfg_part_number,
                variants.c.brand,
                variants.c.internal_sku,
                variants.c.unit_price, # Cargar precio de la variante
                ProductBrand.name.label("brand_name"),
                ProductCategory.name.label("category_name"),
                UOM.name.label("uom_name")
            )
        )

        # Filter by SKU (Main) or Variant Identifiers
        stmt = stmt.where(or_(
            Product.sku == sku,
            variants.c.internal_sku == sku,
            variants.c.mfg_part_number == sku
        ))

        # We take the first match (if multiple, prioritize main product if it matched)
        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        product = row[0]
        
        # Prioridad de precio: 1. Variante, 2. Precio Maestro, 3. 0.0
        variant_price = Decimal(str(row[6])) if row[6] is not None else None
        master_price = Decimal(str(row[1])) if row[1] is not None else None
        
        product.last_price = variant_price if variant_price is not None else (master_price or 0.0)
        product.currency = row[2] or "MXN"
        
        mpn = row[3]
        v_brand = row[4]
        v_sku = row[5]
        
        # Enriched fields
        product.brand_name = row[7] if row[7] else v_brand # fallback to variant brand
        product.category_name = row[8]
        product.uom_name = row[9]

        # Enrich name if it's a variant match
        if sku == mpn or sku == v_sku:
            variant_label = f"({v_brand} {mpn})" if v_brand and mpn else f"({mpn or v_sku})"
            if variant_label not in product.name:
                product.name = f"{product.name} {variant_label}"

        return product

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
    async def get_brands(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        filters = [ProductBrand.company_id == company_id]
        if group_id:
            filters = [or_(ProductBrand.company_id == company_id, ProductBrand.group_id == group_id)]
        
        stmt = select(ProductBrand).where(
            or_(*filters, ProductBrand.company_id == None)
        ).order_by(ProductBrand.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_brand_by_id(self, brand_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        filters = [ProductBrand.company_id == company_id]
        if group_id:
            filters = [or_(ProductBrand.company_id == company_id, ProductBrand.group_id == group_id)]
            
        stmt = select(ProductBrand).where(
            ProductBrand.id == brand_id,
            or_(*filters, ProductBrand.company_id == None)
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
    async def get_categories(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        filters = [ProductCategory.company_id == company_id]
        if group_id:
            filters = [or_(ProductCategory.company_id == company_id, ProductCategory.group_id == group_id)]

        stmt = select(ProductCategory).where(
            or_(*filters, ProductCategory.company_id == None)
        ).order_by(ProductCategory.name)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_category_by_id(self, category_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        filters = [ProductCategory.company_id == company_id]
        if group_id:
            filters = [or_(ProductCategory.company_id == company_id, ProductCategory.group_id == group_id)]

        stmt = select(ProductCategory).where(
            ProductCategory.id == category_id,
            or_(*filters, ProductCategory.company_id == None)
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
    async def get_uoms(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> List[Any]:
        filters = [UOM.company_id == company_id]
        if group_id:
            filters = [or_(UOM.company_id == company_id, UOM.group_id == group_id)]

        stmt = select(UOM).where(
            or_(*filters, UOM.company_id == None)
        ).order_by(UOM.name)
        result = await self.db.execute(stmt)
        uoms = result.scalars().all()
        
        # Lazy Initialization for new companies without UOMs
        if not uoms:
            default_uom = UOM(id=uuid.uuid4(), code="PZ", name="Pieces", abbreviation="PZ", company_id=company_id, tenant_id=company_id, group_id=group_id, version_id=1, is_active=True)
            self.db.add(default_uom)
            await self.db.commit()
            return [default_uom]
            
        return uoms

    async def get_uom_by_id(self, uom_id: uuid.UUID, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        filters = [UOM.company_id == company_id]
        if group_id:
            filters = [or_(UOM.company_id == company_id, UOM.group_id == group_id)]

        stmt = select(UOM).where(
            UOM.id == uom_id,
            or_(*filters, UOM.company_id == None)
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
    # Movement Concepts & Sync
    # =========================================================================
    async def get_concepts(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None, type: Optional[str] = None) -> List[Any]:
        from master_app.models.movement_concept import MovementConcept
        from common.enums import MovementType
        filters = [MovementConcept.company_id == company_id]
        if group_id:
            filters = [or_(MovementConcept.company_id == company_id, MovementConcept.group_id == group_id)]
            
        stmt = select(MovementConcept).where(
            or_(*filters, MovementConcept.company_id == None)
        )
        if type:
            stmt = stmt.where(MovementConcept.type == type)
            
        result = await self.db.execute(stmt)
        concepts = result.scalars().all()
        
        # Lazy Initialization (Just-In-Time Seeding) for new companies without concepts
        if not concepts and not type:
            default_concepts = [
                MovementConcept(id=uuid.uuid4(), name="PURCHASE RECEIPT", code="PUR-REC", type=MovementType.ENTRY, company_id=company_id, tenant_id=company_id, group_id=group_id, version_id=1, is_active=True),
                MovementConcept(id=uuid.uuid4(), name="SALES DISPATCH", code="SAL-DIS", type=MovementType.OUTPUT, company_id=company_id, tenant_id=company_id, group_id=group_id, version_id=1, is_active=True),
                MovementConcept(id=uuid.uuid4(), name="INTERNAL TRANSFER", code="INT-TRA", type=MovementType.TRANSFER, company_id=company_id, tenant_id=company_id, group_id=group_id, version_id=1, is_active=True)
            ]
            self.db.add_all(default_concepts)
            await self.db.commit()
            return default_concepts
            
        return concepts

    async def get_all_master_data(self, company_id: uuid.UUID, group_id: Optional[uuid.UUID] = None) -> dict:
        stmt_products = (
            select(Product)
            .where(or_(Product.company_id == company_id, Product.group_id == group_id) if group_id else Product.company_id == company_id)
            .options(selectinload(Product.versions))
        )
        products_result = await self.db.execute(stmt_products)
        products = products_result.scalars().all()

        uoms = await self.get_uoms(company_id, group_id)

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
