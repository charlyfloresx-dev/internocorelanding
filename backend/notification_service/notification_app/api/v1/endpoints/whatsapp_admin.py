"""
WhatsApp Admin Endpoints
────────────────────────
CRUD for WhatsApp Group Mappings and group discovery utility.

These endpoints are admin-only and allow:
  - Registering a new WhatsApp group mapping for a company.
  - Listing all active mappings for a company.
  - Updating/deactivating a mapping.
  - Sending a test message to verify connectivity.
"""
import uuid
import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from common.responses import ApiResponse
from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from common.security.auth_payload import TokenPayload
from notification_app.models.whatsapp_mapping import WhatsAppGroupMapping

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── SCHEMAS ────────────────────────────────────────────────────────────────

class CreateWhatsAppMappingRequest(BaseModel):
    group_name: str = Field(
        ..., min_length=1, max_length=100,
        description="Nombre lógico del grupo (e.g., 'TECNICOS_PLANTA', 'SUPERVISORES')",
        examples=["TECNICOS_PLANTA"],
    )
    whatsapp_group_id: str = Field(
        ..., min_length=5, max_length=255,
        description="ID externo del grupo de WhatsApp (e.g., '123456789@g.us')",
        examples=["5216621234567-1234567890@g.us"],
    )
    display_name: Optional[str] = Field(
        None, max_length=200,
        description="Nombre legible para la UI (e.g., 'Técnicos - Planta Otay')",
    )


class UpdateWhatsAppMappingRequest(BaseModel):
    whatsapp_group_id: Optional[str] = Field(None, max_length=255)
    display_name: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class TestWhatsAppMessageRequest(BaseModel):
    message: str = Field(
        default="🔧 Mensaje de prueba desde InternoCore Notification Service",
        description="Texto del mensaje de prueba.",
    )


# ─── ENDPOINTS ──────────────────────────────────────────────────────────────

@router.get("/mappings", response_model=ApiResponse)
async def list_whatsapp_mappings(
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los mapeos de grupos de WhatsApp para la empresa del usuario."""
    query = (
        select(WhatsAppGroupMapping)
        .where(WhatsAppGroupMapping.company_id == current_user.company_id)
        .order_by(WhatsAppGroupMapping.group_name)
    )
    result = await db.execute(query)
    mappings = result.scalars().all()

    return ApiResponse(
        status="success",
        data=[m.to_dict() for m in mappings],
        meta={"total": len(mappings)},
    )


@router.post("/mappings", response_model=ApiResponse)
async def create_whatsapp_mapping(
    body: CreateWhatsAppMappingRequest,
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra un nuevo mapeo de grupo de WhatsApp para la empresa.
    El group_name debe ser único por empresa (UniqueConstraint).
    """
    # Verificar si ya existe
    existing = await db.execute(
        select(WhatsAppGroupMapping).where(
            WhatsAppGroupMapping.company_id == current_user.company_id,
            WhatsAppGroupMapping.group_name == body.group_name.upper(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un mapeo para el grupo '{body.group_name}' en esta empresa.",
        )

    mapping = WhatsAppGroupMapping(
        company_id=current_user.company_id,
        group_name=body.group_name.upper(),
        whatsapp_group_id=body.whatsapp_group_id,
        display_name=body.display_name,
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    logger.info(
        f"✅ WhatsApp Mapping created: {body.group_name} -> {body.whatsapp_group_id} "
        f"for company {current_user.company_id}"
    )

    return ApiResponse(
        status="success",
        data=mapping.to_dict(),
        message=f"Grupo '{body.group_name}' registrado exitosamente.",
    )


@router.patch("/mappings/{mapping_id}", response_model=ApiResponse)
async def update_whatsapp_mapping(
    mapping_id: uuid.UUID,
    body: UpdateWhatsAppMappingRequest,
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un mapeo existente (cambiar whatsapp_group_id, display_name, o desactivar)."""
    result = await db.execute(
        select(WhatsAppGroupMapping).where(
            WhatsAppGroupMapping.id == mapping_id,
            WhatsAppGroupMapping.company_id == current_user.company_id,
        )
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(status_code=404, detail="Mapeo no encontrado.")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)

    await db.commit()
    await db.refresh(mapping)

    logger.info(f"📝 WhatsApp Mapping updated: {mapping_id} | Changes: {update_data}")

    return ApiResponse(
        status="success",
        data=mapping.to_dict(),
        message="Mapeo actualizado exitosamente.",
    )


@router.delete("/mappings/{mapping_id}", response_model=ApiResponse)
async def delete_whatsapp_mapping(
    mapping_id: uuid.UUID,
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Elimina un mapeo de grupo de WhatsApp (hard delete)."""
    result = await db.execute(
        select(WhatsAppGroupMapping).where(
            WhatsAppGroupMapping.id == mapping_id,
            WhatsAppGroupMapping.company_id == current_user.company_id,
        )
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(status_code=404, detail="Mapeo no encontrado.")

    await db.delete(mapping)
    await db.commit()

    logger.info(f"🗑️ WhatsApp Mapping deleted: {mapping_id}")

    return ApiResponse(
        status="success",
        message=f"Mapeo '{mapping.group_name}' eliminado exitosamente.",
    )


@router.post("/mappings/{mapping_id}/test", response_model=ApiResponse)
async def test_whatsapp_mapping(
    mapping_id: uuid.UUID,
    body: TestWhatsAppMessageRequest = TestWhatsAppMessageRequest(),
    current_user: TokenPayload = Depends(require_scope(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Envía un mensaje de prueba al grupo de WhatsApp vinculado a este mapeo.
    Útil para verificar que el whatsapp_group_id es correcto antes de usarlo en producción.
    """
    from notification_app.services.notification_service import NotificationService
    from notification_app.infrastructure.whatsapp_client import WhatsAppClient
    from app.core.config import settings

    result = await db.execute(
        select(WhatsAppGroupMapping).where(
            WhatsAppGroupMapping.id == mapping_id,
            WhatsAppGroupMapping.company_id == current_user.company_id,
        )
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(status_code=404, detail="Mapeo no encontrado.")

    if not settings.WHATSAPP_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp API Key no configurada. Revisa las variables de entorno.",
        )

    wa_client = WhatsAppClient(
        account_sid=settings.TWILIO_ACCOUNT_SID,
        auth_token=settings.TWILIO_AUTH_TOKEN,
        sender_number=settings.WHATSAPP_SENDER_NUMBER,
        base_url=settings.WHATSAPP_BASE_URL,
    )

    try:
        svc = NotificationService(db=db, whatsapp_client=wa_client)
        notification = await svc.notify_whatsapp_group(
            company_id=current_user.company_id,
            group_name=mapping.group_name,
            title="🧪 Test de Conectividad",
            message=body.message,
        )
        await db.commit()

        return ApiResponse(
            status="success",
            data=notification.to_dict(),
            message=f"Mensaje de prueba enviado al grupo '{mapping.group_name}'.",
        )

    except Exception as e:
        logger.exception(f"❌ WhatsApp test failed for mapping {mapping_id}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await wa_client.close()


# ─── TWILIO WEBHOOKS ────────────────────────────────────────────────────────

from fastapi import Form

@router.post("/webhook", response_model=None)
async def twilio_whatsapp_webhook(
    From: str = Form(...),
    To: str = Form(...),
    Body: Optional[str] = Form(None),
    SmsStatus: Optional[str] = Form(None),
    MessageSid: Optional[str] = Form(None),
):
    """
    Endpoint para recibir Webhooks de Twilio.
    Maneja dos flujos:
    1. Discovery: Si alguien escribe '/getid' en un grupo, imprimimos el ID.
    2. Status Callback: Si Twilio nos avisa que un mensaje fue entregado/leído.
    """
    
    # FORCED PRINT FOR DISCOVERY (Ensures visibility in user terminal)
    print("\n" + "="*50)
    print(f"📥 INCOMING WHATSAPP MESSAGE")
    print(f"From: {From}")
    print(f"To: {To}")
    print(f"Body: {Body}")
    print(f"Status: {SmsStatus}")
    print("="*50 + "\n")

    # Command detection for group ID discovery
    if Body.strip().lower() == "/getid":
        print(f"🚀 COMMAND DETECTED: /getid")
        print(f"📍 GROUP/SOURCE ID: {From}")
        print("="*50 + "\n")
        return {"message": f"Discovery successful for {From}"}

    # Status Callback flow
    if SmsStatus and MessageSid:
        print(f"📬 Twilio Status Update: {MessageSid} -> {SmsStatus}")

    return {"status": "received"}
