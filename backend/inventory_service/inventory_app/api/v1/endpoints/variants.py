"""
Variant endpoints — thin proxy to master_data_service.
inventory_item_variants table lives in master_data_db as of Phase 118.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
import httpx

from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from common.config import settings

router = APIRouter()

_MD_URL = settings.MASTER_DATA_SERVICE_URL


def _proxy_headers(token: TokenPayload) -> dict:
    return {
        "X-Company-ID": str(token.company_id),
        "Authorization": f"Bearer {getattr(token, '_raw_token', '')}",
    }


@router.get("/products/{product_id}/variants")
async def get_product_variants(
    product_id: uuid.UUID,
    request: Request,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    auth = request.headers.get("Authorization", "")
    headers = {"X-Company-ID": str(token.company_id), "Authorization": auth}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{_MD_URL}/api/v1/products/{product_id}/variants",
            headers=headers,
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


@router.post("/variants")
async def upsert_variant(
    request: Request,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    auth = request.headers.get("Authorization", "")
    headers = {"X-Company-ID": str(token.company_id), "Authorization": auth}
    body = await request.body()
    content_type = request.headers.get("content-type", "application/json")
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{_MD_URL}/api/v1/variants",
            headers={**headers, "content-type": content_type},
            content=body,
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())


@router.delete("/variants/{variant_id}")
async def delete_variant(
    variant_id: uuid.UUID,
    request: Request,
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    auth = request.headers.get("Authorization", "")
    headers = {"X-Company-ID": str(token.company_id), "Authorization": auth}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.delete(
            f"{_MD_URL}/api/v1/variants/{variant_id}",
            headers=headers,
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())
