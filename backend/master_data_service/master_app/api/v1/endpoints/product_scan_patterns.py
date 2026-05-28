from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from master_app.models.product_scan_pattern import ProductScanPattern
from master_app.schemas.product_scan_pattern import ScanPatternCreate, ScanPatternRead, ScanPatternUpdate
from master_app.dependencies import get_db
from common.responses import ApiResponse
from common.domain.entities.user_context import UserContext
from common.security.dependencies import require_scope
from common.security.limiter import limiter

router = APIRouter()


@router.get("/{item_code}/scan-patterns", response_model=ApiResponse[List[ScanPatternRead]])
@limiter.limit("60/minute")
async def list_scan_patterns(
    request: Request,
    item_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_scope(["master_data:read"])),
):
    result = await db.execute(
        select(ProductScanPattern)
        .where(
            ProductScanPattern.item_code == item_code,
            ProductScanPattern.company_id == current_user.company_id,
            ProductScanPattern.is_active == True,
        )
        .order_by(ProductScanPattern.priority)
    )
    patterns = [ScanPatternRead.model_validate(p) for p in result.scalars().all()]
    return ApiResponse(status="success", data=patterns)


@router.post("/{item_code}/scan-patterns", response_model=ApiResponse[ScanPatternRead],
             status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_scan_pattern(
    request: Request,
    item_code: str,
    body: ScanPatternCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_scope(["master_data:write"])),
):
    import re
    try:
        re.compile(body.regex)
    except re.error as exc:
        raise HTTPException(status_code=422, detail=f"Invalid regex: {exc}")

    pattern = ProductScanPattern(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        tenant_id=current_user.company_id,
        item_code=item_code,
        pattern_name=body.pattern_name,
        regex=body.regex,
        error_message=body.error_message,
        priority=body.priority,
        is_active=body.is_active,
    )
    db.add(pattern)
    await db.commit()
    await db.refresh(pattern)
    return ApiResponse(status="success", data=ScanPatternRead.model_validate(pattern),
                       message="Scan pattern created")


@router.patch("/{item_code}/scan-patterns/{pattern_id}", response_model=ApiResponse[ScanPatternRead])
@limiter.limit("30/minute")
async def update_scan_pattern(
    request: Request,
    item_code: str,
    pattern_id: uuid.UUID,
    body: ScanPatternUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_scope(["master_data:write"])),
):
    pattern = await db.get(ProductScanPattern, pattern_id)
    if not pattern or pattern.company_id != current_user.company_id or pattern.item_code != item_code:
        raise HTTPException(status_code=404, detail="Scan pattern not found")

    update_data = body.model_dump(exclude_unset=True)
    if "regex" in update_data:
        import re
        try:
            re.compile(update_data["regex"])
        except re.error as exc:
            raise HTTPException(status_code=422, detail=f"Invalid regex: {exc}")

    for field, value in update_data.items():
        setattr(pattern, field, value)

    await db.commit()
    await db.refresh(pattern)
    return ApiResponse(status="success", data=ScanPatternRead.model_validate(pattern))


@router.delete("/{item_code}/scan-patterns/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_scan_pattern(
    request: Request,
    item_code: str,
    pattern_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_scope(["master_data:write"])),
):
    pattern = await db.get(ProductScanPattern, pattern_id)
    if not pattern or pattern.company_id != current_user.company_id or pattern.item_code != item_code:
        raise HTTPException(status_code=404, detail="Scan pattern not found")

    # Soft-delete: set is_active = False
    pattern.is_active = False
    await db.commit()
    return None
