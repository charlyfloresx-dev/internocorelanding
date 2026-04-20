"""
Inter-Company Transfer — API Endpoints
=======================================
Expone el flujo de Transferencia Inter-Company como endpoints RESTful.

Arquitectura de Seguridad:
  - Todos los endpoints requieren JWT válido (SubscriptionGuard).
  - company_id NUNCA se acepta del body — siempre proviene del token.
  - La validación de pertenencia empresa-almacén ocurre en el Handler.

Endpoints:
  POST   /transfers/inter-company/initiate
           → Empresa A lanza la transferencia (PENDING → SHIPPED)

  POST   /transfers/inter-company/{transfer_id}/receive
           → Empresa B recibe el inventario (SHIPPED → DELIVERED)

  POST   /transfers/inter-company/{transfer_id}/cancel
           → Empresa A cancela antes de la recepción

  GET    /transfers/inter-company/{transfer_id}
           → Consulta el documento (accesible por A y B)

  GET    /transfers/inter-company/inbound/pending
           → Empresa B lista sus transferencias pendientes de recepción

  GET    /transfers/inter-company/outbound
           → Empresa A lista sus transferencias enviadas
"""

import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import (
    InitiateTransferCommand,
    CompleteTransferCommand,
    CancelTransferCommand,
    TransferDocumentEntity,
    PendingTransferEntity,
)
from app.dependencies.repositories import get_inventory_repository
from app.domain.repositories.inventory_repository import IInventoryRepository
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    BusinessRuleException,
    ConflictException,
    DomainException,
    SelfTransferReceiptException,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Dependency Factory ───────────────────────────────────────────────────────

def get_transfer_handler(
    db: AsyncSession = Depends(get_db),
    repo: IInventoryRepository = Depends(get_inventory_repository),
) -> TransferCommandHandler:
    return TransferCommandHandler(session=db, repo=repo)


def _handle_domain_exception(exc: DomainException) -> HTTPException:
    """Mapea DomainException a HTTPException con código apropiado."""
    if isinstance(exc, NotFoundException):
        return HTTPException(status_code=404, detail=exc.message)
    if isinstance(exc, UnauthorizedException):
        return HTTPException(status_code=403, detail=exc.message)
    if isinstance(exc, ConflictException):
        return HTTPException(status_code=409, detail=exc.message)
    if isinstance(exc, BusinessRuleException):
        return HTTPException(status_code=422, detail=exc.message)
    if isinstance(exc, SelfTransferReceiptException):
        return HTTPException(status_code=403, detail=exc.message)
    return HTTPException(status_code=400, detail=exc.message)


# ═════════════════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS (solo los campos que acepta la API — company_id viene del JWT)
# ═════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel, Field
from decimal import Decimal


class InitiateTransferRequest(BaseModel):
    """Body del endpoint de inicio de transferencia inter-company."""
    destination_company_id: uuid.UUID = Field(
        ..., description="Company ID de la empresa DESTINO (Empresa B)"
    )
    destination_warehouse_id: uuid.UUID = Field(
        ..., description="Almacén de destino en Empresa B"
    )
    origin_warehouse_id: uuid.UUID = Field(
        ..., description="Almacén de origen en Empresa A"
    )
    product_id: uuid.UUID = Field(
        ..., description="product_id del catálogo de Empresa A"
    )
    uom_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    weight: Decimal = Field(default=Decimal("0.0"), ge=0)

    # Mapeo de catálogos (SKU Matching)
    origin_sku: Optional[str] = None
    destination_product_id: Optional[uuid.UUID] = Field(
        None, description="product_id equivalente en catálogo de Empresa B"
    )
    destination_sku: Optional[str] = None

    # Metadatos
    notes: Optional[str] = None
    external_reference: Optional[str] = None
    customs_pedimento: Optional[str] = Field(None, max_length=21)
    customs_doc_type: Optional[str] = Field(None, max_length=20)
    currency: str = Field(..., max_length=3, description="Moneda del acuerdo comercial (USD, MXN, etc)")

    # ── Precio de Transferencia (Contrato Financiero) ─────────────────────────
    transfer_price: Optional[Decimal] = Field(
        None,
        gt=0,
        description=(
            "Precio de venta de Empresa A = Costo de compra de Empresa B. "
            "Si no se provee, se usará el WAC de A como fallback (precio sin margen) "
            "y la respuesta incluirá un 'transfer_price_warning'."
        )
    )

    # ── Auditoría y Compliance (Phase 40) ────────────────────────────────────
    exchange_rate_dof: Optional[Decimal] = Field(
        None, gt=0, description="Tasa de cambio oficial para conversión binacional (MXN/USD)"
    )
    risk_acknowledged: Optional[bool] = Field(
        False, description="True si el usuario aceptó explícitamente el riesgo de despacho (ej. pedimento por vencer)"
    )
    selected_batch_id: Optional[uuid.UUID] = None


class ReceiveTransferRequest(BaseModel):
    """Body del endpoint de recepción de transferencia."""
    received_quantity: Optional[Decimal] = Field(
        None, gt=0,
        description="Si None, se asume recepción total de la cantidad despachada"
    )
    damaged_quantity: Decimal = Field(
        default=Decimal("0.0"), ge=0,
        description="Cantidad reportada como dañada (ajuste automático por merma)"
    )
    notes: Optional[str] = Field(None, description="Notas de recepción")
    destination_location: Optional[str] = Field("RECEPTION", description="Ubicación física final en el almacén de destino.")


class CancelTransferRequest(BaseModel):
    """Body del endpoint de cancelación."""
    reason: Optional[str] = Field(None, description="Motivo de la cancelación")


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@router.post(
    "/initiate",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Empresa A] Iniciar transferencia inter-company",
    description=(
        "Crea un documento de tránsito y registra los movimientos de Kardex "
        "correspondientes. El stock sale del almacén de Empresa A y entra a "
        "un hold lógico de tránsito hasta ser recibido por Empresa B."
    ),
)
async def initiate_inter_company_transfer(
    body: InitiateTransferRequest,
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    Requiere:
      - Rol con permiso INVENTORY_CORE en Empresa A.
      - Stock disponible suficiente en el almacén de origen.
    """
    cmd = InitiateTransferCommand(
        origin_company_id=token.company_id,   # ← Del JWT — Zero-Trust
        initiated_by=token.sub,
        destination_company_id=body.destination_company_id,
        destination_warehouse_id=body.destination_warehouse_id,
        origin_warehouse_id=body.origin_warehouse_id,
        product_id=body.product_id,
        uom_id=body.uom_id,
        quantity=body.quantity,
        weight=body.weight,
        origin_sku=body.origin_sku,
        destination_product_id=body.destination_product_id,
        destination_sku=body.destination_sku,
        transfer_price=body.transfer_price,    # ← Precio pactado (puede ser None)
        notes=body.notes,
        external_reference=body.external_reference,
        customs_pedimento=body.customs_pedimento,
        customs_doc_type=body.customs_doc_type,
        exchange_rate_dof=body.exchange_rate_dof,
        risk_acknowledged=body.risk_acknowledged,
        selected_batch_id=body.selected_batch_id,
    )

    try:
        transfer_doc = await handler.initiate_transfer(cmd)
    except DomainException as exc:
        raise _handle_domain_exception(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ApiResponse(
        status="success",
        data=transfer_doc.model_dump(mode="json"),
        message=f"Transferencia inter-company iniciada. Folio: {transfer_doc.folio}",
    )


@router.post(
    "/{transfer_id}/receive",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="[Empresa B] Confirmar recepción de transferencia",
    description=(
        "Empresa B confirma la recepción del inventario en tránsito. "
        "El stock sale del hold de tránsito y entra al almacén físico de Empresa B. "
        "El documento de tránsito se marca como DELIVERED."
    ),
)
async def receive_inter_company_transfer(
    transfer_id: uuid.UUID,
    body: ReceiveTransferRequest,
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    Requiere:
      - Rol con permiso INVENTORY_CORE en Empresa B.
      - El transfer_id debe existir y estar en estado SHIPPED.
      - El company_id del token debe coincidir con destination_company_id del transfer.
    """
    cmd = CompleteTransferCommand(
        receiver_company_id=token.company_id,   # ← Del JWT — Zero-Trust
        received_by=token.sub,
        transfer_id=transfer_id,
        received_quantity=body.received_quantity,
        damaged_quantity=body.damaged_quantity,
        notes=body.notes,
        destination_location=body.destination_location,
    )

    try:
        transfer_doc = await handler.complete_transfer(cmd)
    except DomainException as exc:
        raise _handle_domain_exception(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ApiResponse(
        status="success",
        data=transfer_doc.model_dump(mode="json"),
        message=f"Transferencia {transfer_doc.folio} recibida exitosamente. Stock actualizado en Empresa B.",
    )


@router.post(
    "/{transfer_id}/cancel",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="[Empresa A] Cancelar transferencia en tránsito",
    description=(
        "Cancela una transferencia que aún no ha sido recibida por Empresa B. "
        "El stock es devuelto al almacén de origen de Empresa A."
    ),
)
async def cancel_inter_company_transfer(
    transfer_id: uuid.UUID,
    body: CancelTransferRequest,
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    Requiere:
      - Rol con permiso INVENTORY_CORE en Empresa A (la originadora).
      - El transferido no debe haber sido recibido por B (status != DELIVERED).
    """
    cmd = CancelTransferCommand(
        requester_company_id=token.company_id,  # ← Del JWT — Zero-Trust
        requested_by=token.sub,
        transfer_id=transfer_id,
        reason=body.reason,
    )

    try:
        transfer_doc = await handler.cancel_transfer(cmd)
    except DomainException as exc:
        raise _handle_domain_exception(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ApiResponse(
        status="success",
        data=transfer_doc.model_dump(mode="json"),
        message=f"Transferencia {transfer_doc.folio} cancelada. Stock restaurado en Empresa A.",
    )


@router.post(
    "/{transfer_id}/revert",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="[Empresa A] Reclamar stock de transferencia huérfana",
    description=(
        "Revierte una transferencia SHIPPED que quedó huérfana (Empresa B no la recibió). "
        "El stock regresa del almacén de tránsito al almacén de origen de Empresa A. "
        "El documento DRAFT en Empresa B es cancelado automáticamente."
    ),
)
async def revert_inter_company_transfer(
    transfer_id: uuid.UUID,
    body: CancelTransferRequest,
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    """
    Requiere:
      - Rol con permiso INVENTORY_CORE en Empresa A.
      - El transfer debe estar en estado SHIPPED (no entregado, no cancelado).
    """
    cmd = CancelTransferCommand(
        requester_company_id=token.company_id,
        requested_by=token.sub,
        transfer_id=transfer_id,
        reason=body.reason,
    )

    try:
        transfer_doc = await handler.revert_transfer(cmd)
    except DomainException as exc:
        raise _handle_domain_exception(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ApiResponse(
        status="success",
        data=transfer_doc.model_dump(mode="json"),
        message=f"Transferencia {transfer_doc.folio} revertida. Stock reclamado por Empresa A.",
    )


@router.get(
    "/inbound/pending",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="[Empresa B] Listar transferencias pendientes de recepción",
    description=(
        "Retorna todas las transferencias en estado SHIPPED dirigidas a la empresa "
        "del usuario autenticado. Permite a Empresa B gestionar sus recepciones pendientes."
    ),
)
async def list_pending_inbound_transfers(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    pending = await handler.list_pending_for_company_b(
        company_b_id=token.company_id,
        limit=limit,
        offset=offset,
    )

    return ApiResponse(
        status="success",
        data=[p.model_dump(mode="json") for p in pending],
        message=f"{len(pending)} transferencia(s) pendiente(s) de recepción.",
    )


@router.get(
    "/outbound",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="[Empresa A] Listar transferencias enviadas",
    description=(
        "Retorna el historial de transferencias inter-company generadas por la empresa "
        "del usuario autenticado."
    ),
)
async def list_outbound_transfers(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    transfers = await handler.list_outbound_for_company_a(
        company_a_id=token.company_id,
        limit=limit,
        offset=offset,
    )

    return ApiResponse(
        status="success",
        data=[t.model_dump(mode="json") for t in transfers],
        message=f"{len(transfers)} transferencia(s) saliente(s).",
    )


@router.get(
    "/{transfer_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar documento de transferencia",
    description=(
        "Retorna el detalle completo de una transferencia. "
        "Accesible por ambas empresas involucradas (A y B)."
    ),
)
async def get_transfer_detail(
    transfer_id: uuid.UUID,
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    try:
        transfer_doc = await handler.get_transfer_by_id(
            transfer_id=transfer_id,
            requester_company_id=token.company_id,
        )
    except DomainException as exc:
        raise _handle_domain_exception(exc)

    return ApiResponse(
        status="success",
        data=transfer_doc.model_dump(mode="json"),
        message="Documento de transferencia recuperado.",
    )


@router.get(
    "/by-folio/{folio}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar transferencia por Folio (Scanner)",
    description=(
        "Permite recuperar el detalle de una transferencia usando su número de folio. "
        "Ideal para ser consumido por dispositivos handheld o scanners durante la recepción."
    ),
)
async def get_transfer_by_folio(
    folio: str,
    handler: TransferCommandHandler = Depends(get_transfer_handler),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE")),
):
    try:
        transfer_doc = await handler.get_transfer_by_folio(
            folio=folio,
            requester_company_id=token.company_id,
        )
    except DomainException as exc:
        raise _handle_domain_exception(exc)

    return ApiResponse(
        status="success",
        data=transfer_doc.model_dump(mode="json"),
        message=f"Transferencia {folio} recuperada por escaneo.",
    )
