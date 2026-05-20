import uuid
import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from common.responses import ApiResponse
from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from common.security.auth_payload import TokenPayload
from app.models.whatsapp_mapping import WhatsAppGroupMapping

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
    print(f"\n📥 INCOMING WHATSAPP MESSAGE: {Body} from {From}")
    return {"status": "received"}
