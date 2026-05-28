import uuid
from datetime import date, timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

from hcm_app.core.database import get_db
from hcm_app.core.config import settings
from hcm_app.services.collaborator_service import CollaboratorService
from hcm_app.models.collaborator import Collaborator
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from hcm_app.infrastructure.repositories.collaborator_repository import SQLAlchemyCollaboratorRepository

from hcm_app.schemas.collaborator import (
    CollaboratorCreate,
    CollaboratorRead,
    CollaboratorUpdate,
    EligibilityResponse,
    EligibilityDetail,
)
from common.services.audit_service import AuditService

router = APIRouter()

@router.post("/", response_model=ApiResponse)
async def create_collaborator(
    collaborator_data: CollaboratorCreate,
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    Creates a single collaborator for the current company.
    Enforces per-tenant internal_id pattern validation.
    """
    try:
        repo = SQLAlchemyCollaboratorRepository(db)
        service = CollaboratorService(repo)
        
        # Convert Pydantic to Dict
        data_dict = collaborator_data.model_dump()
        
        result_entity = await service.create_collaborator(data_dict, token.company_id, photo)

        await AuditService.log_action(
            db=db,
            user_id=token.sub,
            action="COLLABORATOR_CREATED",
            entity_name="collaborators",
            entity_id=result_entity.id,
            company_id=token.company_id,
            new_value={"internal_id": result_entity.internal_id, "full_name": result_entity.full_name},
        )
        if collaborator_data.rfid_tag:
            await AuditService.log_action(
                db=db,
                user_id=token.sub,
                action="RFID_ASSIGNED",
                entity_name="collaborators",
                entity_id=result_entity.id,
                company_id=token.company_id,
                details=f"RFID assigned to collaborator {result_entity.internal_id}",
            )

        await db.commit()

        from common import get_storage_provider
        storage = get_storage_provider()
        
        result_read = CollaboratorRead.model_validate(result_entity)
        if result_read.photo_path:
            result_read.profile_url = storage.get_url(result_read.photo_path)
        
        return ApiResponse(
            status="success",
            data=result_read,
            message=f"Collaborator {result_read.full_name} created successfully."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error in create_collaborator")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating collaborator: {str(e)}"
        )

@router.get("/template")
async def get_template():
    """
    Downloads a CSV template for collaborator bulk upload.
    """
    template = await CollaboratorService.get_csv_template()
    filename = "collaborator_template.csv"
    
    return Response(
        content=template,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/bulk-upload", response_model=ApiResponse)
async def bulk_upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    Uploads a CSV file to bulk create/update collaborators for the current company.
    """
    try:
        repo = SQLAlchemyCollaboratorRepository(db)
        service = CollaboratorService(repo)
        results = await service.bulk_upload(file, token.company_id, token.user_id)

        await AuditService.log_action(
            db=db,
            user_id=token.sub,
            action="COLLABORATOR_BULK_UPLOAD",
            entity_name="collaborators",
            entity_id=None,
            company_id=token.company_id,
            details=f"Bulk upload: {results['created']} created, {results['updates']} updated, {len(results['errors'])} errors",
            new_value={"created": results["created"], "updates": results["updates"]},
        )

        await db.commit() # Unit of Work at endpoint level
        
        return ApiResponse(
            status="success",
            data=results,
            message=f"Bulk upload completed: {results['created']} created, {results['updates']} updated."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/search", response_model=ApiResponse[List[CollaboratorRead]])
async def search_collaborators(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    Searches collaborators by name or internal_id.
    """
    stmt = select(Collaborator).where(
        Collaborator.company_id == token.company_id,
        Collaborator.is_active == True
    )
    if q:
        from sqlalchemy import or_
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Collaborator.first_name.ilike(pattern),
                Collaborator.last_name_paternal.ilike(pattern),
                Collaborator.last_name_maternal.ilike(pattern),
                Collaborator.internal_id.ilike(pattern),
            )
        )
    
    result = await db.execute(stmt)
    collaborators = result.scalars().all()
    
    return ApiResponse(
        status="success",
        data=[CollaboratorRead.model_validate(c) for c in collaborators],
        message="Collaborators found"
    )

# ── Phase 50: Handheld Validation Endpoints ────────────────────────────────────

def _check_expiry(value: date | None, label: str, threshold_days: int, today: date) -> EligibilityDetail | None:
    """
    Returns a populated EligibilityDetail if `value` is None, already expired,
    or expiring within the threshold window.
    """
    if value is None:
        return EligibilityDetail(document=label, expiry_date=None, days_remaining=None)
    
    days_remaining = (value - today).days
    if days_remaining < threshold_days:
        return EligibilityDetail(
            document=label,
            expiry_date=value,
            days_remaining=days_remaining
        )
    return None


@router.get("/validate-scan/{badge_id}", response_model=EligibilityResponse)
async def validate_scan(
    badge_id: str,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
    eligibility_type: str = Query(default="CROSS_BORDER", alias="type")
):
    """
    [Phase 50] Fast handheld lookup endpoint.
    Used by the Shipping component to validate a driver by scanning their badge.

    Security: badge_id is ALWAYS filtered by the token's company_id.
    This prevents cross-tenant badge collisions with generic RFID card series.
    """
    # Strict tenant-scoped lookup — no global search allowed
    stmt = select(Collaborator).where(
        Collaborator.internal_id == badge_id,
        Collaborator.company_id == token.company_id,
        Collaborator.is_active == True
    )
    result = await db.execute(stmt)
    collaborator = result.scalar_one_or_none()

    if not collaborator:
        return EligibilityResponse(
            eligible=False,
            reason="Operador no encontrado o inactivo en esta empresa.",
        )

    # Fetch custom safety threshold margin for the company if configured
    repo = SQLAlchemyCollaboratorRepository(db)
    config = await repo.get_tenant_config(token.company_id)
    threshold = config.cross_border_expiry_threshold_days if (config and config.cross_border_expiry_threshold_days is not None) else settings.CROSS_BORDER_EXPIRY_THRESHOLD_DAYS

    # Delegate to the shared eligibility logic
    return _calculate_eligibility(collaborator, eligibility_type, threshold)


@router.get("/{collaborator_id}/eligibility", response_model=EligibilityResponse)
async def get_eligibility(
    collaborator_id: uuid.UUID,
    eligibility_type: str = Query(default="CROSS_BORDER", alias="type"),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    [Phase 50] Validates a collaborator's eligibility for a given operation type.
    Currently supported: CROSS_BORDER.

    Returns a rich object with the first failing document and days remaining,
    so the dispatch operator knows exactly WHY the driver was rejected.
    """
    stmt = select(Collaborator).where(
        Collaborator.id == collaborator_id,
        Collaborator.company_id == token.company_id
    )
    result = await db.execute(stmt)
    collaborator = result.scalar_one_or_none()

    if not collaborator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaborator not found.")

    # Fetch custom safety threshold margin for the company if configured
    repo = SQLAlchemyCollaboratorRepository(db)
    config = await repo.get_tenant_config(token.company_id)
    threshold = config.cross_border_expiry_threshold_days if (config and config.cross_border_expiry_threshold_days is not None) else settings.CROSS_BORDER_EXPIRY_THRESHOLD_DAYS

    return _calculate_eligibility(collaborator, eligibility_type, threshold)


def _calculate_eligibility(collaborator: Collaborator, eligibility_type: str, threshold: int) -> EligibilityResponse:
    """
    Core eligibility logic. Evaluates all relevant documents against today's date
    with a configurable grace period (cross_border_expiry_threshold_days / CROSS_BORDER_EXPIRY_THRESHOLD_DAYS).

    Priority order: Critical docs are checked first (License > Medical > Visa > Sentry/Global Entry).
    The first failing document short-circuits and is returned in `details`.
    """
    today = date.today()
    full_name = collaborator.full_name

    if eligibility_type == "CROSS_BORDER":
        # Priority order — first failure wins
        checks = [
            _check_expiry(collaborator.driver_license_expiry, "Licencia Comercial (CDL/Federal)", threshold, today),
            _check_expiry(collaborator.medical_certificate_expiry, "Certificado Médico (SCT/DOT)", threshold, today),
            _check_expiry(collaborator.visa_expiry, "Visa Láser / B1-B2", threshold, today),
        ]

        for failing_doc in checks:
            if failing_doc is not None:
                days = failing_doc.days_remaining
                if days is None:
                    reason = f"Documento no registrado: {failing_doc.document}."
                elif days < 0:
                    reason = f"{failing_doc.document} expirado hace {abs(days)} día(s)."
                else:
                    reason = f"{failing_doc.document} vence en {days} día(s) (margen de seguridad: {threshold} días)."

                return EligibilityResponse(
                    eligible=False,
                    reason=reason,
                    collaborator_id=collaborator.id,
                    full_name=full_name,
                    details=failing_doc
                )

        # Enforce that either sentry_id or global_entry_id is present and active (non-empty)
        sentry_ok = collaborator.sentry_id is not None and len(collaborator.sentry_id.strip()) > 0
        global_entry_ok = hasattr(collaborator, "global_entry_id") and collaborator.global_entry_id is not None and len(collaborator.global_entry_id.strip()) > 0

        if not (sentry_ok or global_entry_ok):
            return EligibilityResponse(
                eligible=False,
                reason="Operador requiere credencial FAST/Sentry o Global Entry activa para cruce internacional.",
                collaborator_id=collaborator.id,
                full_name=full_name,
                details=EligibilityDetail(
                    document="FAST/Sentry o Global Entry ID",
                    expiry_date=None,
                    days_remaining=None
                )
            )

        return EligibilityResponse(
            eligible=True,
            reason="Documentación vigente y dentro del margen de seguridad.",
            collaborator_id=collaborator.id,
            full_name=full_name,
        )

    # Default: basic active check for non-cross-border operations
    if not collaborator.is_active:
        return EligibilityResponse(
            eligible=False,
            reason="Operador inactivo en el sistema.",
            collaborator_id=collaborator.id,
            full_name=full_name,
        )

    return EligibilityResponse(
        eligible=True,
        reason="Operador activo.",
        collaborator_id=collaborator.id,
        full_name=full_name,
    )
