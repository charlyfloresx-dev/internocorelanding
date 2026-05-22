import uuid
import logging
from typing import Optional
from pydantic import BaseModel, Field
import httpx
from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from common.responses import ApiResponse
from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from common.security.auth_payload import TokenPayload
from app.models.whatsapp_mapping import WhatsAppGroupMapping
from app.core.config import settings

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Admin"])
logger = logging.getLogger(__name__)

# --- SCHEMAS ---
class CreateWhatsAppMappingRequest(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=100)
    whatsapp_group_id: str = Field(..., min_length=5, max_length=255)
    display_name: Optional[str] = Field(None, max_length=200)

class UpdateWhatsAppMappingRequest(BaseModel):
    whatsapp_group_id: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None

class TestWhatsAppMessageRequest(BaseModel):
    to: str = Field(..., description="Número de teléfono destino (+52XXXXXXXXXX) o group JID (XXXX@g.us)")
    message: str = Field(default="🔧 Mensaje de prueba desde InternoCore Notification Service")

# --- ENDPOINTS ---
@router.get("/mappings", response_model=ApiResponse)
async def list_whatsapp_mappings(
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    query = select(WhatsAppGroupMapping).where(WhatsAppGroupMapping.company_id == current_user.company_id).order_by(WhatsAppGroupMapping.group_name)
    result = await db.execute(query)
    mappings = result.scalars().all()
    return ApiResponse(status="success", data=[m.to_dict() for m in mappings])

@router.post("/mappings", response_model=ApiResponse)
async def create_whatsapp_mapping(
    body: CreateWhatsAppMappingRequest,
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    mapping = WhatsAppGroupMapping(
        company_id=current_user.company_id,
        group_name=body.group_name.upper(),
        whatsapp_group_id=body.whatsapp_group_id,
        display_name=body.display_name,
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return ApiResponse(status="success", data=mapping.to_dict())

@router.post("/webhook", response_model=None)
async def twilio_whatsapp_webhook(
    From: str = Form(...),
    To: str = Form(...),
    Body: Optional[str] = Form(None),
    SmsStatus: Optional[str] = Form(None),
    MessageSid: Optional[str] = Form(None),
):
    print(f"\n INCOMING WHATSAPP MESSAGE: {Body} from {From}")
    return {"status": "received"}


# ---------------------------------------------------------------------------
# Proxy espejo seguro — ADR-02
# company_id se toma SIEMPRE del JWT verificado (Muro de Hierro multitenancy)
# El cliente nunca puede consultar ni alterar sesiones de otro tenant
# ---------------------------------------------------------------------------

def _gateway_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_GATEWAY_API_KEY}",
        "Content-Type": "application/json",
    }


async def _proxy_get(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{settings.LOCAL_WHATSAPP_GATEWAY_URL.rstrip('/')}{path}",
                headers=_gateway_headers()
            )
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WhatsApp Gateway unreachable: {str(e)}"
        )


async def _proxy_post(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.LOCAL_WHATSAPP_GATEWAY_URL.rstrip('/')}{path}",
                headers=_gateway_headers()
            )
        return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WhatsApp Gateway unreachable: {str(e)}"
        )


@router.get("/session/status", response_model=ApiResponse)
async def get_session_status(
    current_user: TokenPayload = Depends(require_scope(["admin", "notifications:manage"])),
):
    """Retorna el estado de la sesión WhatsApp del tenant autenticado."""
    data = await _proxy_get(f"/api/v1/whatsapp/session/{current_user.company_id}/status")
    return ApiResponse(status="success", data=data)


@router.get("/session/qr", response_model=ApiResponse)
async def get_session_qr(
    current_user: TokenPayload = Depends(require_scope(["admin", "notifications:manage"])),
):
    """Retorna el QR de vinculación para el tenant autenticado (estado QR_READY)."""
    data = await _proxy_get(f"/api/v1/whatsapp/session/{current_user.company_id}/qr")
    return ApiResponse(status="success", data=data)


@router.post("/test-send", response_model=ApiResponse)
async def test_send_message(
    body: TestWhatsAppMessageRequest,
    current_user: TokenPayload = Depends(require_scope(["admin"])),
):
    """Envía un mensaje de prueba desde la sesión del tenant autenticado."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.LOCAL_WHATSAPP_GATEWAY_URL.rstrip('/')}/api/v1/whatsapp/send",
                headers=_gateway_headers(),
                json={
                    "company_id": str(current_user.company_id),
                    "to": body.to,
                    "message": body.message,
                },
            )
        return ApiResponse(status="success", data=resp.json())
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WhatsApp Gateway unreachable: {str(e)}"
        )


@router.post("/session/initialize", response_model=ApiResponse)
async def initialize_session(
    current_user: TokenPayload = Depends(require_scope(["admin", "notifications:manage"])),
):
    """Inicializa (o reinicia) la sesión WhatsApp del tenant autenticado."""
    data = await _proxy_post(f"/api/v1/whatsapp/session/{current_user.company_id}/initialize")
    return ApiResponse(status="success", data=data)
