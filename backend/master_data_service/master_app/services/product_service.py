import uuid
import logging
from typing import List, Optional, Any
from uuid import UUID
from fastapi import UploadFile
from decimal import Decimal

from master_app.domain.repositories.master_data_repository import IMasterDataRepository
from master_app.schemas.product import ProductCreate
from common.exceptions import BusinessRuleException, NotFoundException
from common.domain import ProductStatus, VersionStatus
from common.context import request_context
from common import get_storage_provider

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, repo: IMasterDataRepository):
        self.repo = repo

    async def get_products_by_company(self, company_id: UUID, group_id: Optional[UUID] = None, q: Optional[str] = None, warehouse_id: Optional[UUID] = None) -> List[Any]:
        """Retrieves company products with optional search filter."""
        from common import get_storage_provider
        storage = get_storage_provider()
        
        products = await self.repo.get_products(company_id, group_id, q=q, warehouse_id=warehouse_id)
        
        # Inject pre-signed URLs
        for p in products:
            if hasattr(p, 'photo_path') and p.photo_path:
                p.product_url = storage.get_url(p.photo_path)
            else:
                p.product_url = None
                
        return products

    async def get_product_by_id(self, product_id: Any, company_id: Any) -> Any:
        """Gets a specific product validating the tenant."""
        p_id = uuid.UUID(str(product_id)) if not isinstance(product_id, uuid.UUID) else product_id
        c_id = uuid.UUID(str(company_id)) if not isinstance(company_id, uuid.UUID) else company_id

        product = await self.repo.get_product_by_id(p_id, c_id)
        if not product:
            raise NotFoundException("Product not found")
            
        # Inject pre-signed URL
        if hasattr(product, 'photo_path') and product.photo_path:
            from common import get_storage_provider
            storage = get_storage_provider()
            product.product_url = storage.get_url(product.photo_path)
        else:
            product.product_url = None
            
        return product

    async def lookup_product_by_code(self, code: str, company_id: UUID, partner_id: Optional[UUID] = None) -> Any:
        """Lookup product by SKU or Barcode for POS Scanning, with dynamic price resolution."""
        product = await self.repo.get_product_by_sku(code, company_id)
        if not product:
            return None
            
        # Inject pre-signed URL
        if hasattr(product, 'photo_path') and product.photo_path:
            from common import get_storage_provider
            storage = get_storage_provider()
            product.product_url = storage.get_url(product.photo_path)
        else:
            product.product_url = None
            
        # Resolve Price (Phase 2 POS - Onion Layers Hierarchy)
        from master_app.api.v1.endpoints.prices import resolve_price
        # We simulate a dependency-less call to the resolver logic
        # Actually, it's better to have a internal_resolve_price function, 
        # but for now we'll fetch the global price (List 1) or Agreement.
        
        from master_app.models.product_price import ProductPrice
        from master_app.models.price_agreement import PriceAgreement
        from master_app.models.partner import Partner
        from sqlalchemy import select, and_
        
        resolved_price = None
        
        # 1. B2B Agreement
        if partner_id:
            ag_stmt = select(PriceAgreement).where(
                and_(
                    PriceAgreement.product_id == product.id,
                    PriceAgreement.partner_id == partner_id,
                    PriceAgreement.company_id == company_id,
                    PriceAgreement.valid_until.is_(None)
                )
            )
            ag_res = await self.repo.db.execute(ag_stmt)
            agreement = ag_res.scalars().first()
            if agreement:
                resolved_price = agreement.amount

        # 2. Assigned List / Global
        if resolved_price is None:
            target_list = 1
            if partner_id:
                p_stmt = select(Partner.price_list_index).where(Partner.id == partner_id)
                p_res = await self.repo.db.execute(p_stmt)
                target_list = p_res.scalars().first() or 1
                
            pr_stmt = select(ProductPrice).where(
                and_(
                    ProductPrice.product_id == product.id,
                    ProductPrice.company_id == company_id,
                    ProductPrice.price_list_index == target_list,
                    ProductPrice.warehouse_id.is_(None),
                    ProductPrice.is_active == True
                )
            ).order_by(ProductPrice.created_at.desc())
            pr_res = await self.repo.db.execute(pr_stmt)
            price_obj = pr_res.scalars().first()
            if price_obj:
                resolved_price = price_obj.price.amount
            elif target_list != 1:
                # Fallback to List 1
                fb_stmt = select(ProductPrice).where(
                    and_(
                        ProductPrice.product_id == product.id,
                        ProductPrice.company_id == company_id,
                        ProductPrice.price_list_index == 1,
                        ProductPrice.warehouse_id.is_(None),
                        ProductPrice.is_active == True
                    )
                ).order_by(ProductPrice.created_at.desc())
                fb_res = await self.repo.db.execute(fb_stmt)
                fb_price = fb_res.scalars().first()
                if fb_price:
                    resolved_price = fb_price.price.amount

        if resolved_price:
            # Set price on the transient product object
            product.price = {"amount": Decimal(str(resolved_price)), "currency": "MXN"}
        else:
            product.price = {"amount": 0.0, "currency": "MXN"}

        return product


    async def create_product(self, product_in: ProductCreate, photo: Optional[UploadFile] = None) -> Any:
        """Creates a product and its initial version atomically, with optional photo."""
        user_ctx = request_context.get()
        if not user_ctx or not user_ctx.company_id or not user_ctx.user_id:
            raise BusinessRuleException("User or company context not found.")

        company_id = user_ctx.company_id
        user_id = user_ctx.user_id
        product_id = uuid.uuid4()

        photo_path = None
        if photo:
            try:
                storage = get_storage_provider()
                # Path: {company_id}/inventory/products/{uuid}.jpg
                extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
                object_key = f"{company_id}/inventory/products/{product_id}.{extension}"
                
                # Upload
                photo_path = storage.upload_file(photo.file, object_key, content_type=photo.content_type)
                logger.info(f"Photo uploaded for product {product_in.sku}: {photo_path}")
            except Exception as e:
                logger.error(f"Error uploading photo for product {product_in.sku}: {str(e)}")

        product_data = {
            "id": product_id,
            "company_id": company_id,
            "group_id": product_in.group_id or getattr(user_ctx, 'group_id', None),
            "sku": product_in.sku,
            "name": product_in.name,
            "description": product_in.description,
            "product_type": product_in.product_type,
            "category_id": product_in.category_id,
            "brand_id": product_in.brand_id,
            "photo_path": photo_path,
            # Physical
            "requires_batch": product_in.requires_batch,
            "requires_expiration": product_in.requires_expiration,
            # Fiscal
            "sat_product_code": product_in.sat_product_code,
            "hts_code": product_in.hts_code,
            "is_taxable": product_in.is_taxable,
            "allow_price_override": product_in.allow_price_override,
            "status": ProductStatus.DRAFT,
            "created_by": user_id,
            "updated_by": user_id,
        }
        version_data = {
            "company_id": company_id,
            "version_number": 1,
            "um_id": product_in.uom_id,
            "version_status": VersionStatus.DESIGN,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id,
        }
        return await self.repo.create_product(product_data, version_data)

    async def approve_version(self, product_id: UUID, version_number: int, company_id: UUID) -> Any:
        """Approves a version for production."""
        version = await self.repo.approve_version(product_id, version_number, company_id)
        if not version:
            raise NotFoundException("Product version not found.")
        return version
    async def update_product(self, product_id: UUID, company_id: UUID, update_data: dict) -> Any:
        """Updates a product."""
        product = await self.repo.update_product(product_id, company_id, update_data)
        if not product:
            raise NotFoundException("Product not found.")
        return product

    async def delete_product(self, product_id: UUID, company_id: UUID) -> None:
        """Soft-deletes a product."""
        await self.repo.delete_product(product_id, company_id)
