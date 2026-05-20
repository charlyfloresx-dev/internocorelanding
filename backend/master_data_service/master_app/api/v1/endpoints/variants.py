import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from master_app.models.item_variant import ItemVariant
from master_app.dependencies import get_db
from common.security.dependencies import require_scope
from common.responses import ApiResponse
from common.domain.entities.user_context import UserContext
from pydantic import BaseModel, Field
from fastapi import Security
from common import get_storage_provider

router = APIRouter()


class ItemVariantCreate(BaseModel):
    product_id: uuid.UUID
    internal_sku: str
    brand: str = Field(..., description="Brand or Supplier Name")
    mfg_part_number: str = Field(..., description="Manufacturer Part Number")
    unit_price: Decimal = Decimal("0.0")
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    is_preferred: bool = False
    photo_path: Optional[str] = None


class ItemVariantRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    internal_sku: str
    brand: str
    mfg_part_number: str
    unit_price: Decimal
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    is_preferred: bool
    photo_path: Optional[str] = None
    product_url: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/products/{product_id}/variants", response_model=ApiResponse[List[ItemVariantRead]])
async def get_product_variants(
    product_id: uuid.UUID,
    current_user: UserContext = Security(require_scope(["master_data:read"])),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ItemVariant).where(
            ItemVariant.product_id == product_id,
            ItemVariant.company_id == current_user.company_id,
        )
    )
    variants = result.scalars().all()
    storage = get_storage_provider()
    out = []
    for v in variants:
        d = ItemVariantRead.model_validate(v)
        d.product_url = storage.get_url(v.photo_path) if v.photo_path else None
        out.append(d)
    return ApiResponse(data=out)


@router.post("/variants", response_model=ApiResponse[ItemVariantRead])
async def upsert_variant(
    variant_in: ItemVariantCreate,
    photo: Optional[UploadFile] = File(None),
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    db: AsyncSession = Depends(get_db),
):
    photo_path = None
    if photo:
        try:
            storage = get_storage_provider()
            variant_id = uuid.uuid4()
            ext = photo.filename.split('.')[-1] if photo.filename and '.' in photo.filename else 'jpg'
            key = f"{current_user.company_id}/inventory/variants/{variant_id}.{ext}"
            photo_path = storage.upload_file(photo.file, key, content_type=photo.content_type)
        except Exception:
            pass

    existing = await db.execute(
        select(ItemVariant).where(
            ItemVariant.company_id == current_user.company_id,
            ItemVariant.internal_sku == variant_in.internal_sku,
            ItemVariant.mfg_part_number == variant_in.mfg_part_number,
        )
    )
    variant = existing.scalar_one_or_none()

    if variant:
        variant.brand = variant_in.brand
        variant.unit_price = variant_in.unit_price
        variant.weight = variant_in.weight
        variant.volume = variant_in.volume
        variant.is_preferred = variant_in.is_preferred
        if photo_path:
            variant.photo_path = photo_path
    else:
        variant = ItemVariant(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            tenant_id=current_user.company_id,
            product_id=variant_in.product_id,
            internal_sku=variant_in.internal_sku,
            brand=variant_in.brand,
            mfg_part_number=variant_in.mfg_part_number,
            unit_price=variant_in.unit_price,
            weight=variant_in.weight,
            volume=variant_in.volume,
            is_preferred=variant_in.is_preferred,
            photo_path=photo_path or variant_in.photo_path,
        )
        db.add(variant)

    await db.commit()
    await db.refresh(variant)

    storage = get_storage_provider()
    out = ItemVariantRead.model_validate(variant)
    out.product_url = storage.get_url(variant.photo_path) if variant.photo_path else None
    return ApiResponse(data=out, message="Variant saved successfully")


@router.delete("/variants/{variant_id}", response_model=ApiResponse)
async def delete_variant(
    variant_id: uuid.UUID,
    current_user: UserContext = Security(require_scope(["master_data:write"])),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(ItemVariant).where(
            ItemVariant.id == variant_id,
            ItemVariant.company_id == current_user.company_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    await db.commit()
    return ApiResponse(message="Variant deleted")
