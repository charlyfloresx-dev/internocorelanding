import uuid
import logging
from typing import List, Optional, Any
from uuid import UUID
from fastapi import UploadFile

from app.domain.repositories.inventory_repository import IInventoryRepository
from app.schemas.variant import ItemVariantCreate
from common.exceptions import BusinessRuleException, NotFoundException
from common import get_storage_provider

logger = logging.getLogger(__name__)

class VariantService:
    def __init__(self, repo: IInventoryRepository):
        self.repo = repo

    async def get_variants_by_product(self, product_id: UUID, company_id: UUID) -> List[Any]:
        """Retrieves variants with pre-signed URLs."""
        storage = get_storage_provider()
        variants = await self.repo.get_variants_by_product(product_id, company_id)
        
        for v in variants:
            if hasattr(v, 'photo_path') and v.photo_path:
                v.product_url = storage.get_url(v.photo_path)
            else:
                v.product_url = None
        return variants

    async def upsert_variant(self, variant_in: ItemVariantCreate, company_id: UUID, photo: Optional[UploadFile] = None) -> Any:
        """Creates or updates a variant with optional photo upload."""
        variant_id = getattr(variant_in, 'id', uuid.uuid4())
        
        photo_path = None
        if photo:
            try:
                storage = get_storage_provider()
                # Path: {company_id}/inventory/variants/{uuid}.jpg
                extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
                object_key = f"{company_id}/inventory/variants/{variant_id}.{extension}"
                
                # Upload
                photo_path = storage.upload_file(photo.file, object_key, content_type=photo.content_type)
                logger.info(f"Photo uploaded for variant {variant_in.internal_sku}: {photo_path}")
            except Exception as e:
                logger.error(f"Error uploading photo for variant {variant_in.internal_sku}: {str(e)}")

        variant_data = variant_in.model_dump()
        if photo_path:
            variant_data["photo_path"] = photo_path
        
        variant = await self.repo.upsert_variant(variant_data, company_id)
        
        # Inject URL for response
        if variant.photo_path:
            storage = get_storage_provider()
            variant.product_url = storage.get_url(variant.photo_path)
        else:
            variant.product_url = None
            
        return variant
