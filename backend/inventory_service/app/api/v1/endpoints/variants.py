import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile

from app.db.session import get_db
from app.schemas.variant import ItemVariantRead, ItemVariantCreate, VariantListResponse
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.services.variant_service import VariantService
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from app.dependencies.repositories import get_variant_service

router = APIRouter()

@router.get("/products/{product_id}/variants", response_model=VariantListResponse)
async def get_product_variants(
    product_id: uuid.UUID,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    service: VariantService = Depends(get_variant_service),
):
    """
    Retrieves all variants (Supplier Item Mappings) for a master product.
    """
    variants = await service.get_variants_by_product(product_id, token.company_id)
    return ApiResponse(status="success", data=variants)

@router.post("/variants", response_model=ApiResponse)
async def upsert_variant(
    variant_in: ItemVariantCreate,
    photo: Optional[UploadFile] = File(None),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    service: VariantService = Depends(get_variant_service),
):
    """
    Creates or updates a Product Variant (Supplier mapping).
    """
    variant = await service.upsert_variant(variant_in, token.company_id, photo=photo)
    
    return ApiResponse(
        status="success",
        message="Variant saved successfully",
        data=ItemVariantRead.model_validate(variant)
    )

@router.delete("/variants/{variant_id}", response_model=ApiResponse)
async def delete_variant(
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    Deletes a Product Variant.
    """
    from app.models.item_variant import ItemVariant
    from sqlalchemy import delete
    
    stmt = delete(ItemVariant).where(
        ItemVariant.id == variant_id,
        ItemVariant.company_id == token.company_id
    )
    result = await session.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Variant not found")
        
    await session.commit()
    return ApiResponse(status="success", message="Variant deleted")
