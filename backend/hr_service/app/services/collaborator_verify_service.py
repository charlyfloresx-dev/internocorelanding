import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_rfid, verify_rfid, verify_pin
from app.repositories.collaborator_repository import CollaboratorRepository
from app.schemas.collaborator import CollaboratorVerifyRequest, CollaboratorVerifyResponse, CollaboratorMultiVerifyResponse

logger = logging.getLogger(__name__)


async def verify_collaborator(
    request: CollaboratorVerifyRequest,
    db: AsyncSession,
) -> Optional[CollaboratorMultiVerifyResponse]:
    """
    Core verification logic. Checks RFID or PIN against stored hashes.
    Returns a list of matching identities (MultiVerifyResponse).
    """
    repo = CollaboratorRepository(db)
    collaborators = []

    if request.rfid_tag:
        rfid_hash = hash_rfid(request.rfid_tag)
        # 1. Local attempt by RFID
        collaborators = await repo.get_by_rfid(rfid_hash, request.company_id)
        
        # 2. Global Discovery by RFID
        if not collaborators and not request.company_id:
            collaborators = await repo.get_by_rfid(rfid_hash, None)
            
    elif request.internal_id:
        # 1. Local attempt by Internal ID (Barcode)
        collaborators = await repo.get_by_internal_id(request.internal_id, request.company_id)
        
        # 2. Global Discovery by Internal ID
        if not collaborators and not request.company_id:
            logger.info(f"🔍 ID {request.internal_id} no encontrado localmente. Intentando descubrimiento global...")
            collaborators = await repo.get_by_internal_id(request.internal_id, None)

        # 3. Collaborative PIN Verification (if provided)
        if request.pin_code:
            valid_matches = []
            for c in collaborators:
                if verify_pin(request.pin_code, c.pin_code):
                    valid_matches.append(c)
            collaborators = valid_matches
        else:
            # Si NO se provee PIN, solo permitimos si el colaborador NO TIENE pin configurado?
            # O permitimos login 1-factor por ID (Barcode) por requerimiento del usuario.
            logger.info(f"🔓 Login 1-factor detectado para ID: {request.internal_id}")
            pass # Mantenemos la lista de encontrados

    elif request.pin_code:
        # Fallback: Si llega solo PIN, podría ser un escaneo de código de barras 
        # enviado al campo equivocado por el frontend. Intentamos buscar por ID.
        logger.info(f"⚠️ Detectado PIN sin ID. Intentando tratar PIN como ID: {request.pin_code}")
        collaborators = await repo.get_by_internal_id(request.pin_code, request.company_id)
        if not collaborators and not request.company_id:
            collaborators = await repo.get_by_internal_id(request.pin_code, None)

    elif request.collaborator_id:
        # Búsqueda Directa por UUID (Flujo de Select Company)
        c = await repo.get_by_id(request.collaborator_id, request.company_id)
        if c:
            collaborators = [c]
        else:
            # FALLBACK INDUSTRIAL: Salto de empresa para colaboradores multi-tenant
            # Si el ID del token (ej. Luis MX) no coincide con la empresa elegida (ej. Logistic US),
            # buscamos si Luis tiene una identidad en la empresa elegida usando su RFID/ID.
            base_c = await repo.get_just_by_id(request.collaborator_id)
            if base_c:
                if base_c.rfid_tag:
                    collaborators = await repo.get_by_rfid(base_c.rfid_tag, request.company_id)
                elif base_c.internal_id:
                    collaborators = await repo.get_by_internal_id(base_c.internal_id, request.company_id)
            else:
                collaborators = []

    if not collaborators:
        return None

    matches = []
    for collaborator in collaborators:
        is_supervisor = collaborator.supervisor_id is None
        matches.append(CollaboratorVerifyResponse(
            collaborator_id=collaborator.id,
            internal_id=collaborator.internal_id,
            full_name=collaborator.full_name,
            home_warehouse_id=collaborator.home_warehouse_id,
            department=collaborator.department,
            is_supervisor=is_supervisor,
            company_id=collaborator.company_id,
            tenant_id=collaborator.tenant_id,
        ))

    return CollaboratorMultiVerifyResponse(
        matches=matches,
        count=len(matches)
    )
