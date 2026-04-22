"""
Transfer Domain Entities & Pydantic Schemas
============================================
Define los Value Objects y DTOs del flujo de Transferencia Inter-Company.

Arquitectura:
  - InitiateTransferCommand   → Empresa A lanza la transferencia (PENDING → SHIPPED)
  - CompleteTransferCommand   → Empresa B recibe el inventario (SHIPPED → DELIVERED)
  - TransferDocumentEntity    → Vista de lectura del documento de tránsito
  - TransferLineEntity        → Partida dentro de una transferencia

Principios:
  - Cada comando lleva su propio company_id para Zero-Trust multitenancy.
  - El CompleteTransferCommand valida que destination_company_id == contexto del usuario.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from common.domain.value_objects import Money

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Enums de Dominio ──────────────────────────────────────────────────────────

class MovementType(str, enum.Enum):
    """Tipos de movimiento de Kardex para transferencias."""
    TRANSFER_OUT     = "TRANSFER_OUT"      # Empresa A: salida física → en tránsito
    TRANSFER_IN      = "TRANSFER_IN"       # Empresa B: tránsito → entrada física
    TRANSFER         = "TRANSFER"          # Generic transfer
    TRANSIT_HOLD     = "TRANSIT_HOLD"      # Registro lógico del hold en tránsito
    TRANSIT_RELEASE  = "TRANSIT_RELEASE"   # Liberación del hold de tránsito

class TransferStatusEnum(str, enum.Enum):
    PENDING   = "PENDING"
    SHIPPED   = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# ─── AuditBase ─────────────────────────────────────────────────────────────────

class AuditBase(BaseModel):
    """
    Base de auditoría reutilizable para cualquier documento de dominio.
    Provee campos estándar de trazabilidad forense.
    """
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


# ─── Comando: Empresa A — Iniciar Transferencia ───────────────────────────────

class InitiateTransferCommand(BaseModel):
    """
    Comando emitido por un usuario de la Empresa A para iniciar una
    transferencia inter-company.

    Flujo resultante:
      1. Descuenta stock del origin_warehouse en Empresa A.
      2. Registra movimiento TRANSFER_OUT en Kardex de A.
      3. Acredita en almacén lógico IN_TRANSIT (propiedad de Empresa B).
      4. Crea documento InterCompanyTransfer con status=SHIPPED.
    """
    # ── Contexto de Seguridad (Zero-Trust) ──
    origin_company_id: uuid.UUID = Field(
        ...,
        description="Company ID de la Empresa A (extraído del JWT — no confiar en el body)"
    )
    initiated_by: uuid.UUID = Field(
        ...,
        description="User ID del despachador en Empresa A"
    )

    # ── Destino ────────────────────────────────────────────────────────────────
    destination_company_id: uuid.UUID = Field(
        ...,
        description="Company ID de la Empresa B que recibirá el inventario"
    )
    destination_warehouse_id: uuid.UUID = Field(
        ...,
        description="Almacén físico de destino en Empresa B"
    )

    # ── Origen ─────────────────────────────────────────────────────────────────
    origin_warehouse_id: uuid.UUID = Field(
        ...,
        description="Almacén físico de origen en Empresa A"
    )

    # ── Producto ───────────────────────────────────────────────────────────────
    product_id: uuid.UUID = Field(
        ...,
        description="product_id del catálogo de Empresa A"
    )
    uom_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0, description="Cantidad positiva a transferir")
    weight: Decimal = Field(default=Decimal("0.0"), ge=0)

    # ── SKU Cross-Company (Mapeo de Catálogos) ─────────────────────────────────
    origin_sku: Optional[str] = Field(
        None,
        description="SKU del producto en el catálogo de Empresa A"
    )
    destination_product_id: Optional[uuid.UUID] = Field(
        None,
        description="product_id equivalente en el catálogo de Empresa B (mapeo previo)"
    )
    destination_sku: Optional[str] = Field(
        None,
        description="SKU equivalente en Empresa B para conciliación"
    )

    # ── PRECIO DE TRANSFERENCIA (Contrato Financiero) ────────────────────────────
    transfer_price: Optional[Decimal] = Field(
        None,
        gt=0,
        description=(
            "Precio pactado entre Empresa A y Empresa B por unidad. "
            "PRECIO DE VENTA de A = COSTO DE COMPRA de B. "
            "Si no se provee, el sistema usará el WAC de A como fallback "
            "y generará una advertencia (transfer_price_warning en la respuesta)."
        )
    )

    # ── Metadatos ─────────────────────────────────────────────────────────────
    concept_id: Optional[uuid.UUID] = Field(None, description="ID del concepto de movimiento (INT-TRA)")
    notes: Optional[str] = None
    external_reference: Optional[str] = Field(
        default=None,
        description="Número de guía, orden de compra u otro ref externo"
    )
    # ── Documentación Aduanera (Binacional) ────────────────────────────────────
    customs_pedimento: Optional[str] = Field(
        None, max_length=21, description="Número de Pedimento"
    )
    customs_doc_type: Optional[str] = Field(
        None, max_length=20, description="Tipo de documento aduanal"
    )
    currency: str = Field(default="USD", max_length=3, description="Moneda acordada para el ICT")

    # ── Auditoría y Compliance (Phase 40) ────────────────────────────────────
    exchange_rate_dof: Optional[Decimal] = Field(
        None, description="Tasa de cambio oficial para conversión binacional (MXN/USD)"
    )
    risk_acknowledged: Optional[bool] = Field(
        False, description="True si el usuario aceptó explícitamente el riesgo de despacho"
    )
    selected_batch_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def validate_cross_company(self) -> "InitiateTransferCommand":
        # Commented out to allow Flow 3 (Internal Transfers within Same Company)
        # if self.origin_company_id == self.destination_company_id:
        #     raise ValueError(
        #         "ERR_SAME_COMPANY_TRANSFER: origin_company_id y destination_company_id "
        #         "no pueden ser la misma empresa. Use una transferencia intra-company."
        #     )
        return self

    @model_validator(mode="after")
    def validate_warehouse_mismatch(self) -> "InitiateTransferCommand":
        if self.origin_warehouse_id == self.destination_warehouse_id:
            raise ValueError(
                "ERR_SAME_WAREHOUSE: Los almacenes de origen y destino no pueden ser el mismo."
            )
        return self


# ─── Comando: Empresa B — Completar/Recibir Transferencia ─────────────────────

class CompleteTransferCommand(BaseModel):
    """
    Comando emitido por un usuario de la Empresa B para confirmar la recepción
    del inventario en tránsito.

    Validaciones de Seguridad (Zero-Trust):
      - receiver_company_id DEBE coincidir con destination_company_id del documento.
      - El sistema rechaza si el usuario no pertenece a la empresa destino.

    Flujo resultante:
      1. Valida que transfer_id.destination_company_id == receiver_company_id.
      2. Descuenta stock del IN_TRANSIT (warehouse lógico).
      3. Acredita en destination_warehouse en Empresa B.
      4. Registra movimiento TRANSFER_IN en Kardex de B.
      5. Actualiza InterCompanyTransfer a status=DELIVERED.
    """
    # ── Contexto de Seguridad ──────────────────────────────────────────────────
    receiver_company_id: uuid.UUID = Field(
        ...,
        description="Company ID de la Empresa B (extraído del JWT)"
    )
    received_by: uuid.UUID = Field(
        ...,
        description="User ID del receptor en Empresa B"
    )

    # ── Referencia al Documento de Tránsito ───────────────────────────────────
    transfer_id: uuid.UUID = Field(
        ...,
        description="ID del InterCompanyTransfer creado por Empresa A"
    )

    # ── Recepción ─────────────────────────────────────────────────────────────
    received_quantity: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Si None, se asume la cantidad original del documento (recepción total)."
    )
    concept_id: Optional[uuid.UUID] = Field(None, description="ID del concepto de movimiento (INT-TRA)")
    damaged_quantity: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="Cantidad reportada como dañada durante la recepción."
    )
    notes: Optional[str] = Field(
        None,
        description="Observaciones de recepción (daños, faltantes, etc.)"
    )
    destination_location: Optional[str] = Field(
        "RECEPTION",
        description="Ubicación física final en el almacén de destino (Density Guard check)."
    )
    customs_pedimento_id: Optional[uuid.UUID] = Field(
        None,
        description="ID del Pedimento (Anexo 24) vinculado formalmente al momento de recibir (opcional)"
    )


# ─── Comando: Empresa A — Cancelar Transferencia ─────────────────────────────

class CancelTransferCommand(BaseModel):
    """
    Comando para cancelar una transferencia ANTES de que Empresa B la reciba.
    Solo aplica a documentos en estado PENDING o SHIPPED.
    Solo puede ser ejecutado por un usuario de la Empresa A originadora.
    """
    requester_company_id: uuid.UUID = Field(
        ...,
        description="Company ID de quien cancela (debe ser Empresa A)"
    )
    requested_by: uuid.UUID
    transfer_id: uuid.UUID
    reason: Optional[str] = Field(None, description="Motivo de la cancelación")


# ─── Entidades de Respuesta / Read Models ─────────────────────────────────────

class TransferPartyEntity(BaseModel):
    """Representa a una parte (Empresa A o B) en el documento de tránsito."""
    company_id: uuid.UUID
    warehouse_id: uuid.UUID
    warehouse_name: Optional[str] = None
    sku: Optional[str] = None
    product_id: Optional[uuid.UUID] = None


class TransferDocumentEntity(BaseModel):
    """
    Vista completa de un InterCompanyTransfer para respuestas API.
    Puede ser leída por ambas empresas (con datos filtrados por contexto).
    """
    id: uuid.UUID
    folio: str
    status: TransferStatusEnum

    origin: TransferPartyEntity
    destination: TransferPartyEntity

    product_id: uuid.UUID
    uom_id: uuid.UUID
    quantity: Decimal
    weight: Decimal
    currency: str = "MXN"

    # ── Bloque Financiero (Money VO) ──────────────────────────────────────────
    unit_price_at_dispatch: Optional[Money] = Field(
        None,
        description="Precio de transferencia SELLADO al despacho (A->B)."
    )
    wac_at_dispatch: Optional[Money] = Field(
        None,
        description="WAC real de Empresa A al despacho."
    )
    transfer_revenue_a: Optional[Money] = Field(
        None,
        description="Ingreso contable interno de Empresa A."
    )
    acquisition_cost_b: Optional[Money] = Field(
        None,
        description="Costo de adquisición de Empresa B."
    )
    transfer_margin_a: Optional[Money] = Field(
        None,
        description="Margen bruto interno de A (Socio Virtual)."
    )
    price_source: Optional[str] = Field(
        None,
        description="Origen del precio: EXPLICIT | WAC_FALLBACK | DEFAULT_FALLBACK"
    )
    transfer_price_warning: Optional[str] = Field(
        None,
        description="Advertencia si no se proveyó un transfer_price explícito."
    )
    # ─────────────────────────────────────────────────────────────

    received_quantity: Optional[Decimal] = None
    damaged_quantity: Decimal = Decimal("0.0")
    notes: Optional[str] = None
    external_reference: Optional[str] = None
    customs_pedimento: Optional[str] = None
    customs_doc_type: Optional[str] = None

    # Trazabilidad y Compliance (Phase 40)
    pending_financial_valuation: bool = False
    audit_notes: Optional[str] = None
    exchange_rate_dof: Optional[Decimal] = None
    customs_pedimento_id: Optional[uuid.UUID] = None

    dispatch_movement_id: Optional[uuid.UUID] = None
    receive_movement_id: Optional[uuid.UUID] = None

    created_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    received_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PendingTransferEntity(BaseModel):
    """
    Vista resumida de una transferencia pendiente de recepción.
    Expuesta al dashboard de la Empresa B para gestionar recepciones.
    """
    id: uuid.UUID
    folio: str
    status: TransferStatusEnum
    origin_company_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    weight: Decimal
    shipped_at: Optional[datetime] = None
    external_reference: Optional[str] = None
    notes: Optional[str] = None
    origin_sku: Optional[str] = None
    destination_sku: Optional[str] = None

    class Config:
        from_attributes = True


class TransferKardexEntry(BaseModel):
    """
    Entrada de Kardex específica para movimientos de transferencia inter-company.
    Extiende el concepto de KardexRowEntity con campos de cross-company.
    """
    movement_id: uuid.UUID
    date: str
    folio: str
    movement_type: MovementType
    quantity_delta: Decimal       # Positivo = entrada, Negativo = salida
    uom_id: uuid.UUID
    weight: Decimal
    unit_price: Money
    running_balance: Decimal

    # Cross-company metadata
    origin_company_id: uuid.UUID
    destination_company_id: uuid.UUID
    transfer_id: uuid.UUID
