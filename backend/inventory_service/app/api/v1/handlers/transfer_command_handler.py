"""
TransferCommandHandler — CQRS Handler
======================================
Handler principal para el flujo de Transferencia Inter-Company.

Implementa el patrón de Entidad Intermediaria de Tránsito (Trusted Broker):
  - InitiateTransfer (Empresa A): Descuenta stock de A, acredita en tránsito.
  - CompleteTransfer (Empresa B): Descuenta tránsito, acredita en almacén de B.
  - CancelTransfer  (Empresa A): Revierte la operación de despacho si no recibido.

Principios de Clean Architecture:
  - Usa IInventoryRepository para acceso a datos (inversión de dependencias).
  - Usa TransferService para la mecánica de movimientos atómicos.
  - Lanza excepciones de dominio (DomainException) en vez de HTTP exceptions.
  - La lógica de seguridad (Zero-Trust) reside aquí, no en la capa API.
"""

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from common.domain.value_objects import Money

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
import sqlalchemy as sa

from common.services.audit_service import AuditService

from app.domain.entities.transfer_entities import (
    InitiateTransferCommand,
    CompleteTransferCommand,
    CancelTransferCommand,
    TransferDocumentEntity,
    TransferPartyEntity,
    PendingTransferEntity,
    TransferStatusEnum,
    MovementType,
)
from common.messaging import EventPublisher
from common.services.master_data_client import master_data_client
from common.services.notification_client import notification_client
from app.domain.entities.inventory_item import MovementEntity
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.models.inter_company_transfer import InterCompanyTransfer, TransferStatus
from app.models.document import InventoryDocument, DocumentStatus
from app.models.movement import Movement
from app.models.warehouse import Warehouse
from app.domain.services.fifo_discharge_service import FIFODischargeService
from app.domain.services.transfer_audit_service import TransferAuditService
from common.exceptions import (
    DomainException,
    NotFoundException,
    UnauthorizedException,
    BusinessRuleException,
    ConflictException,
    SelfTransferReceiptException,
)

logger = logging.getLogger(__name__)


def _generate_folio() -> str:
    """
    Genera un folio determinístico para el documento de transferencia inter-company.
    Formato: ICT-{YYYYMMDD}-{SHORT_UUID}
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_id = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"ICT-{today}-{short_id}"


def _transit_warehouse_id(destination_warehouse_id: uuid.UUID) -> uuid.UUID:
    """
    Genera el UUID determinístico del almacén lógico de tránsito.
    Consistente con el TransferService existente.
    """
    return uuid.uuid5(uuid.NAMESPACE_OID, f"{destination_warehouse_id}_transit")


async def _resolve_transfer_price(
    requested_price: Optional[Decimal],
    current_wac: Decimal,
    product_id: uuid.UUID,
    origin_company_id: uuid.UUID,
    destination_company_id: uuid.UUID,
) -> tuple[Decimal, str, Optional[str]]:
    """
    Resuelve el precio de transferencia con 3 niveles de fallback.
    Retorna: (price, source, warning_message)

    Nivel 1 — EXPLICIT:
      El despachador proveyó un `transfer_price` explícito.
      Es el caso ideal: el precio está pactado y es el contrato financiero.

    Nivel 2 — WAC_FALLBACK:
      No hay precio explícito. Usamos el WAC actual de Empresa A.
      Esto significa que A vende "a costo", sin margen.
      Se genera una ADVERTENCIA para que el usuario sepa que no hay margen.

    Nivel 3 — DEFAULT_FALLBACK:
      El WAC también es cero (sin historial de entradas con precio).
      Usamos 1.0 como precio mínimo para evitar que el stock viaje con costo cero
      y arruine el WAC de la Empresa B.
      Se genera una ADVERTENCIA CRITICA.
    """
    # Nivel 1: Precio explícito del despachador
    if requested_price and requested_price > 0:
        return requested_price, "EXPLICIT", None

    # Nivel 2: WAC de Empresa A como fallback
    if current_wac > 0:
        warning = (
            f"TRANSFER_PRICE_WARNING: No se proporcionó un precio de transferencia explícito. "
            f"Usando WAC de Empresa A ({current_wac}) como costo de entrada para Empresa B. "
            f"Esto implica que Empresa A vende a costo sin margen. "
            f"Se recomienda definir una lista de precios inter-company."
        )
        logger.warning(f"[ICT][PRICING] {warning} | product={product_id}")
        return current_wac, "WAC_FALLBACK", warning

    # Nivel 3: DEFAULT_FALLBACK crítico
    MIN_TRANSFER_PRICE = Decimal("1.0")
    warning = (
        f"TRANSFER_PRICE_CRITICAL: No hay precio explícito NI WAC disponible para "
        f"Producto {product_id} de Empresa {origin_company_id}. "
        f"Usando precio mínimo de seguridad ({MIN_TRANSFER_PRICE}) para evitar WAC=0 en Empresa B. "
        f"ACCIÓN REQUERIDA: Definir precios inter-company o registrar entradas con costo."
    )
    logger.error(f"[ICT][PRICING] {warning}")
    return MIN_TRANSFER_PRICE, "DEFAULT_FALLBACK", warning


class TransferCommandHandler:
    """
    Handler CQRS para todos los comandos del flujo inter-company.

    Dependencias:
      - session: AsyncSession de SQLAlchemy (Unit of Work pattern)
      - repo: IInventoryRepository para acceder a stock y movimientos
    """

    def __init__(self, session: AsyncSession, repo: IInventoryRepository):
        self.session = session
        self.repo = repo
        self.fifo_service = FIFODischargeService()
        self.audit_svc = TransferAuditService(self.repo) # New decoupled audit

    async def _check_location_capacity(self, warehouse_id: uuid.UUID, location_code: str, quantity: Decimal, company_id: uuid.UUID):
        """
        [Phase 63] Master Data SSOT Density Guard: Validates location capacity using structural metadata.
        No longer uses local repo, calls Master Data Service via internal API client.
        """
        if not location_code or quantity <= 0:
            return

        # SSOT: Fetch capacity from Master Data Service
        capacity = await master_data_client.get_location_capacity(warehouse_id, location_code, company_id)
        
        if capacity > 0:
            occupancy = await self.repo.get_location_occupancy(warehouse_id, location_code, company_id)
            if occupancy + quantity > capacity:
                logger.warning(f"🚨 DENSITY_GUARD_VIOLATION: Location {location_code} overflows in WH {warehouse_id}. Cap: {capacity}, Current: {occupancy}, New: {quantity}")
                
                # Notification Flow: Dispatch ComplianceViolationEvent
                await notification_client.send_event(
                    event_type="ComplianceViolationEvent",
                    payload={
                        "violation_type": "DENSITY_OVERFLOW",
                        "warehouse_id": str(warehouse_id),
                        "location_code": location_code,
                        "capacity": float(capacity),
                        "occupancy": float(occupancy),
                        "requested": float(quantity),
                        "severity": "HIGH"
                    },
                    company_id=str(company_id)
                )

                raise BusinessRuleException(
                    message=f"ERR_LOCATION_OVERFLOW: La ubicación {location_code} no tiene espacio disponible.",
                    details={
                        "capacity": str(capacity),
                        "occupancy": str(occupancy),
                        "requested": str(quantity),
                        "excess": str((occupancy + quantity) - capacity)
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # COMANDO 1: InitiateTransfer (Empresa A)
    # ═══════════════════════════════════════════════════════════════════════════

    async def initiate_transfer(
        self, cmd: InitiateTransferCommand
    ) -> TransferDocumentEntity:
        """
        Empresa A inicia la transferencia:
        1. Valida stock disponible en origin_warehouse.
        2. Registra TRANSFER_OUT en Kardex de A (stock físico disminuye).
        3. Registra en almacén lógico IN_TRANSIT vinculado a Empresa B.
        4. Crea el documento InterCompanyTransfer con status=SHIPPED.

        Seguridad Zero-Trust:
          - origin_company_id es extraído del JWT en la capa API, nunca del body.
          - El handler valida que origin_warehouse pertenece a origin_company.
        """
        logger.info(
            f"[ICT] InitiateTransfer: Company {cmd.origin_company_id} → "
            f"Company {cmd.destination_company_id} | "
            f"Product {cmd.product_id} | Qty {cmd.quantity}"
        )

        # Pre-initialize variables used after the transaction block
        # to avoid UnboundLocalError if an exception is raised inside.
        transfer_id = uuid.uuid4()
        transfer_doc = None
        transfer_price = None
        price_source = "UNKNOWN"


        async with self.session.begin():
            # ── 0. Validaciones de Almacén ──────────────────────────
            # Resolver almacén de destino si se envió el genérico de "Delegado" (UUID de ceros)
            EMPTY_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

            is_delegated = cmd.destination_warehouse_id == EMPTY_UUID
            
            if is_delegated:
                # Buscar el primer almacén físico disponible de la empresa destino
                stmt_fallback = select(Warehouse).filter_by(
                    company_id=cmd.destination_company_id, 
                    is_transit=False
                ).limit(1)
                fallback_wh = (await self.session.execute(stmt_fallback)).scalar_one_or_none()
                if not fallback_wh:
                    raise BusinessRuleException(f"ERR_WAREHOUSE_NOT_FOUND: La empresa receptora no tiene almacenes físicos configurados.")
                
                # Actualizar el comando y la variable local para que el resto de la lógica use este ID real
                cmd.destination_warehouse_id = fallback_wh.id
                dest_wh = fallback_wh
                logger.info(f"[ICT] Destination delegated. Resolved to {dest_wh.name} ({dest_wh.id})")
            else:
                stmt_dest = select(Warehouse).filter_by(id=cmd.destination_warehouse_id, company_id=cmd.destination_company_id)
                dest_wh = (await self.session.execute(stmt_dest)).scalar_one_or_none()
                if not dest_wh:
                    raise BusinessRuleException(f"ERR_WAREHOUSE_NOT_FOUND: Almacén de destino {cmd.destination_warehouse_id} no existe.")

            # ── 0.A Resolver almacén de origen ────────────────────────────────
            stmt_origin = select(Warehouse).filter_by(id=cmd.origin_warehouse_id, company_id=cmd.origin_company_id)
            origin_wh = (await self.session.execute(stmt_origin)).scalar_one_or_none()
            if not origin_wh:
                raise BusinessRuleException(f"ERR_WAREHOUSE_NOT_FOUND: Almacén de origen {cmd.origin_warehouse_id} no existe.")

            # ── 0.B AGENTE DE AUDITORÍA PRE-VUELO ─────────────────────────────
            # Audit is now decoupled from session, uses repo.
            audit_result = await self.audit_svc.execute_preflight_audit(cmd, origin_wh, dest_wh)

            if audit_result.is_rejected():
                raise BusinessRuleException(
                    message=f"ERR_PREFLIGHT_REJECTED: La auditoría pre-vuelo rechazó la transferencia.",
                    details=audit_result.to_dict()
                )

            if audit_result.warnings:
                logger.warning(
                    f"[ICT][AUDIT] Transferencia con advertencias de cumplimiento: "
                    f"{[w.code for w in audit_result.warnings]}"
                )

            # LÓGICA COMPLIANCE BINACIONAL:
            is_binational = audit_result.is_binational
            logger.info(f"[ICT][AUDIT] Compliance Status resolved: is_binational={is_binational} | pending_fin={audit_result.pending_financial_valuation}")
            
            if is_binational and not cmd.customs_pedimento and not audit_result.pending_financial_valuation:
                raise BusinessRuleException(
                    message=(
                        f"ERR_CUSTOMS_REQUIRED: La transferencia internacional entre empresas "
                        f"requiere número de Pedimento o Export Entry para cumplir con el Anexo 24/30. "
                        f"Clave sugerida: {audit_result.suggested_customs_key}"
                    )
                )

            # ── 0. Forensic Check: Asegurar que los almacenes existen localmente ──
            transit_wh_id = _transit_warehouse_id(cmd.destination_warehouse_id)
            
            # Verificar tránsito
            stmt_wh = select(Warehouse).filter_by(id=transit_wh_id, company_id=cmd.destination_company_id)
            res_wh = await self.session.execute(stmt_wh)
            if not res_wh.scalar_one_or_none():
                logger.info(f"[ICT] Creando almacén lógico de tránsito {transit_wh_id} para Empresa B.")
                transit_wh = Warehouse(
                    id=transit_wh_id,
                    company_id=cmd.destination_company_id,
                    tenant_id=cmd.destination_company_id, # Simplified Multi-tenancy
                    code="TRANSIT",
                    name="Virtual Transit Warehouse",
                    location="INTER-SERVICE-NETWORK",
                    is_transit=True  # Segmentación física clara
                )
                self.session.add(transit_wh)
                await self.session.flush()

            # ── 1. Validar stock disponible en Empresa A ───────────────────────────
            try:
                current_stock = await self.repo.get_stock(
                    warehouse_id=cmd.origin_warehouse_id,
                    product_id=cmd.product_id,
                    company_id=cmd.origin_company_id,
                )
            except Exception as e:
                raise BusinessRuleException(
                    message=f"ERR_STOCK_ACCESS_DENIED: No se pudo verificar el stock de origen.",
                    details={"warehouse_id": str(cmd.origin_warehouse_id), "error": str(e)},
                )

            available_qty = (
                current_stock.quantity - current_stock.reserved_quantity
                if current_stock
                else Decimal("0.0")
            )

            if available_qty < cmd.quantity:
                raise BusinessRuleException(
                    message=(
                        f"ERR_INSUFFICIENT_STOCK: Stock disponible insuficiente para la transferencia. "
                        f"Disponible: {available_qty}, Solicitado: {cmd.quantity}"
                    ),
                    details={
                        "available": str(available_qty),
                        "requested": str(cmd.quantity),
                        "product_id": str(cmd.product_id),
                        "warehouse_id": str(cmd.origin_warehouse_id),
                    },
                )

            # ── 2. Obtener WAC actual de Empresa A (costo real de A) ────
            try:
                wac_data = await self.repo.get_wac_valuation(
                    product_id=cmd.product_id,
                    warehouse_id=cmd.origin_warehouse_id,
                    company_id=cmd.origin_company_id,
                )
                current_wac = wac_data.wac if wac_data else Money(Decimal("0.0"), cmd.currency)
            except Exception:
                current_wac = Money(Decimal("0.0"), cmd.currency)
                logger.warning(f"[ICT] WAC no disponible para {cmd.product_id} en {cmd.origin_warehouse_id}.")

            # ── 3. Precio de Transferencia — Compliance Aware ──────────────────
            # Si el Agente detectó MISSING_PRICE, usamos $0.00 y marcamos como deuda.
            # Si hay precio explícito o WAC, lo utilizamos como base financiera.
            explicit_price = getattr(cmd, "transfer_price", None)
            if explicit_price and Decimal(str(explicit_price)) > 0:
                transfer_price_val = Decimal(str(explicit_price))
                price_source = "EXPLICIT"
            elif audit_result.pending_financial_valuation:
                transfer_price_val = Decimal("0.0")  # Deuda administrativa
                price_source = "PENDING_VALUATION"
            elif current_wac.amount > 0:
                transfer_price_val = current_wac.amount
                price_source = "WAC_A"
            else:
                transfer_price_val = Decimal("0.0")
                price_source = "DEFAULT_ZERO"

            # Conversión FX si es binacional (precio en USD para la entidad espejo)
            if audit_result.is_binational and audit_result.applied_fx_rate:
                transfer_price_usd = TransferAuditService.compute_usd_amount(
                    transfer_price_val, cmd.currency, audit_result.applied_fx_rate
                )
                mirror_currency = "USD"
            else:
                transfer_price_usd = transfer_price_val
                mirror_currency = cmd.currency

            transfer_price = Money(amount=transfer_price_val, currency=cmd.currency)

            # Calcular ingresos de A y margen interno
            transfer_revenue_a = Money(amount=(cmd.quantity * transfer_price.amount).quantize(Decimal("0.0001")), currency=cmd.currency)
            margin_a = (transfer_revenue_a.amount - (cmd.quantity * current_wac.amount)).quantize(Decimal("0.0001"))
            transfer_margin_a = Money(amount=margin_a, currency=cmd.currency)

            logger.info(
                f"[ICT][PRICING] Precio resuelto: {transfer_price} ({price_source}) | "
                f"WAC_A={current_wac} | Revenue_A={transfer_revenue_a} | Margen_A={transfer_margin_a}"
            )
            # Resolve pricing warning for entity response
            price_warning = None
            if audit_result.warnings:
                price_warning = "; ".join([f"{w.code}: {w.msg}" for w in audit_result.warnings])

            transfer_id = uuid.uuid4()
            
            # ── 4. Movimiento(s) TRANSFER_OUT en Empresa A (Partición FIFO Anexo 24) ──
            try:
                logger.debug(f"[ICT][FIFO] Requesting discharge plan: product={cmd.product_id}, qty={cmd.quantity}, strict={audit_result.is_binational}")
                discharge_plan = await self.fifo_service.get_discharge_plan(
                    inventory_repo=self.repo,
                    product_id=cmd.product_id,
                    warehouse_id=cmd.origin_warehouse_id,
                    requested_qty=cmd.quantity,
                    company_id=cmd.origin_company_id,
                    strict=audit_result.is_binational,
                    selected_batch_id=cmd.selected_batch_id
                )
            except BusinessRuleException as e:
                raise e
            except Exception as e:
                logger.error(f"[FIFO] Fallo al calcular plan de descargo: {str(e)}")
                raise DomainException(f"ERR_FIFO_PLAN_FAILURE: No se pudo calcular la partición de lotes/pedimentos.")

            first_out_movement_id = None
            primary_pedimento_id = None
            
            for instr in discharge_plan:
                out_movement_id = uuid.uuid4()
                if not first_out_movement_id:
                    first_out_movement_id = out_movement_id
                    primary_pedimento_id = instr.customs_pedimento_id
                    
                out_movement = MovementEntity(
                    id=out_movement_id,
                    warehouse_id=cmd.origin_warehouse_id,
                    product_id=cmd.product_id,
                    company_id=cmd.origin_company_id,
                    quantity=-instr.quantity_to_discharge,
                    uom_id=cmd.uom_id,
                    weight=cmd.weight * (instr.quantity_to_discharge / cmd.quantity),
                    price=transfer_price,
                    movement_type=MovementType.TRANSFER_OUT.value,
                    document_type="ICT_DISPATCH",
                    document_id=transfer_id,
                    source_movement_id=instr.source_movement_id,
                    customs_pedimento_id=instr.customs_pedimento_id
                )

                await self.repo.record_movement(out_movement)
                
                # CONSUMIR SALDO (Phase 42.0: Skip if Ghost Stock)
                if instr.source_movement_id:
                    stmt_update = (
                        sa.update(Movement)
                        .where(Movement.id == instr.source_movement_id)
                        .values(available_quantity=Movement.available_quantity - instr.quantity_to_discharge)
                    )
                    await self.session.execute(stmt_update)
                else:
                    logger.warning(f"[FIFO] Outbound movement {out_movement_id} recorded WITHOUT source consumption (Ghost Stock).")

            # ── 5. Movimiento TRANSIT_HOLD (Entrada al limbo) ──────────────────────
            transit_movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transit_wh_id,
                product_id=cmd.destination_product_id or cmd.product_id,
                company_id=cmd.destination_company_id,
                quantity=cmd.quantity,
                uom_id=cmd.uom_id,
                weight=cmd.weight,
                price=transfer_price,
                movement_type=MovementType.TRANSIT_HOLD.value,
                document_type="ICT_TRANSIT_IN",
                document_id=transfer_id,
            )

            await self.repo.record_movement(transit_movement, allow_negative=True)

            # ── 6. Auditoría y Compliance Data ──────────────────────────────────────
            import json
            audit_notes_json = json.dumps(audit_result.to_dict()) if (audit_result.warnings or audit_result.pending_financial_valuation) else None

            # ── 7. Crear documento InterCompanyTransfer ────────────────────────────────
            folio_base = _generate_folio()
            transfer_doc = InterCompanyTransfer(
                id=transfer_id,
                folio=folio_base,
                company_id=cmd.origin_company_id,
                tenant_id=cmd.origin_company_id,
                destination_company_id=cmd.destination_company_id,
                origin_warehouse_id=cmd.origin_warehouse_id,
                destination_warehouse_id=cmd.destination_warehouse_id,
                transit_warehouse_id=transit_wh_id,
                product_id=cmd.product_id,
                uom_id=cmd.uom_id,
                quantity=cmd.quantity,
                weight=cmd.weight,
                currency=cmd.currency,
                unit_price=transfer_price,
                wac_origin=current_wac,
                revenue_a=transfer_revenue_a,
                status=TransferStatus.SHIPPED,
                shipped_at=datetime.now(timezone.utc),
                shipped_by=cmd.initiated_by,
                origin_sku=cmd.origin_sku,
                destination_sku=cmd.destination_sku,
                destination_product_id=cmd.destination_product_id,
                notes=cmd.notes,
                external_reference=cmd.external_reference,
                customs_pedimento=cmd.customs_pedimento,
                customs_pedimento_id=primary_pedimento_id, # Formal ID
                customs_doc_type=cmd.customs_doc_type,
                dispatch_movement_id=first_out_movement_id,
                created_by=cmd.initiated_by,
                # Phase 40 Fields
                pending_financial_valuation=audit_result.pending_financial_valuation,
                audit_notes=audit_notes_json,
                exchange_rate_dof=audit_result.applied_fx_rate,
            )

            # ── 8. LÓGICA ESPEJO (Phase 33.5): Documentos de Auditoría ──────────────
            out_doc_id = uuid.uuid4()
            out_doc = InventoryDocument(
                id=out_doc_id,
                company_id=cmd.origin_company_id,
                tenant_id=cmd.origin_company_id,
                folio=f"STR-{folio_base}",
                document_type="ICT_OUT",
                status=DocumentStatus.PROCESSED,
                origin_name="STOCK",
                destination_name=f"TRANSFER TO {cmd.destination_company_id}",
                total_items=1,
                total_weight=cmd.weight,
                total_amount=transfer_revenue_a,
                external_reference=f"OUT-{transfer_id}",
                created_by=cmd.initiated_by,
                pending_financial_valuation=audit_result.pending_financial_valuation,
                audit_notes=audit_notes_json,
            )

            # Monto espejo en USD si es binacional
            mirror_amount = Money(amount=transfer_price_usd * cmd.quantity, currency=mirror_currency)

            mirror_doc_id = uuid.uuid4()
            mirror_folio = f"IN-{folio_base}"
            mirror_doc = InventoryDocument(
                id=mirror_doc_id,
                company_id=cmd.destination_company_id,
                tenant_id=cmd.destination_company_id,
                folio=mirror_folio,
                document_type="ICT_IN",
                status=DocumentStatus.DRAFT,
                origin_name=f"TRANSFER FROM {cmd.origin_company_id}",
                destination_name="STOCK",
                total_items=1,
                total_weight=cmd.weight,
                total_amount=mirror_amount,
                external_reference=f"IN-{transfer_id}",
                created_by=cmd.initiated_by,
                pending_financial_valuation=audit_result.pending_financial_valuation,
                audit_notes=audit_notes_json,
            )
            
            transfer_doc.mirror_document_id = mirror_doc_id
            transfer_doc.inbound_folio = mirror_folio

            self.session.add(transfer_doc)
            self.session.add(out_doc)
            self.session.add(mirror_doc)
            # await self.session.flush() # Not strictly needed with async with begin() but safe

        # ── 8. Publicar Evento de Dominio ─────────────────────────────────────
        # Guard: si la transacción fue interrumpida (BusinessRuleException), no publicar.
        if not transfer_doc:
            return None

        publisher = EventPublisher()
        await publisher.publish("TransferInitiatedEvent", {
            "transfer_id": str(transfer_id),
            "origin_company": str(cmd.origin_company_id),
            "dest_company": str(cmd.destination_company_id),
            "folio": transfer_doc.folio
        })


        await AuditService.log_action(
            db=self.session,
            action="CREATE_INTER_COMPANY_TRANSFER",
            user_id=cmd.initiated_by,
            entity_name="InterCompanyTransfer",
            entity_id=str(transfer_doc.id),
            details=str({"folio": transfer_doc.folio, "transfer_price": str(transfer_price)})
        )

        logger.info(
            f"[ICT] InterCompanyTransfer creado: folio={transfer_doc.folio} | "
            f"status={transfer_doc.status} | ID={transfer_id} | "
            f"transfer_price={transfer_price} ({price_source})"
        )

        entity = self._to_document_entity(transfer_doc)
        # Inyectar campos de auditoría de precio que no están en el modelo
        entity.price_source = price_source
        entity.transfer_price_warning = price_warning
        entity.transfer_margin_a = transfer_margin_a
        return entity

    # ═══════════════════════════════════════════════════════════════════════════
    # COMANDO 2: CompleteTransfer (Empresa B)
    # ═══════════════════════════════════════════════════════════════════════════

    async def complete_transfer(
        self, cmd: CompleteTransferCommand
    ) -> TransferDocumentEntity:
        """
        Empresa B confirma la recepción del inventario en tránsito:
        1. Valida que transfer.destination_company_id == receiver_company_id (Zero-Trust).
        2. Saca stock del almacén lógico IN_TRANSIT.
        3. Acredita en destination_warehouse de Empresa B.
        4. Registra TRANSFER_IN en Kardex de B.
        5. Actualiza el documento a status=DELIVERED.

        El handler rechaza si:
          - El transfer no existe o ya fue procesado (idempotencia).
          - El receiver_company_id no coincide con destination_company_id.
          - El estado no es SHIPPED.
        """
        async with self.session.begin():
            # ── 1. Recuperar el documento de tránsito ─────────────────────────────
            stmt = select(InterCompanyTransfer).where(
                InterCompanyTransfer.id == cmd.transfer_id
            )
            result = await self.session.execute(stmt)
            transfer = result.scalar_one_or_none()

            if not transfer:
                raise NotFoundException(
                    message=f"ERR_TRANSFER_NOT_FOUND: No existe un documento de transferencia con ID {cmd.transfer_id}.",
                    details={"transfer_id": str(cmd.transfer_id)},
                )

            # ── 2. ZERO-TRUST: Validar que el receptor pertenece a la Empresa B ───
            if transfer.destination_company_id != cmd.receiver_company_id:
                logger.warning(
                    f"[ICT][SECURITY] ACCESO NO AUTORIZADO al transfer {cmd.transfer_id}. "
                    f"Empresa del receptor: {cmd.receiver_company_id}, "
                    f"Empresa destino del transfer: {transfer.destination_company_id}"
                )
                raise UnauthorizedException(
                    message=(
                        "ERR_UNAUTHORIZED_RECEIVER: La empresa del usuario no es la destinataria "
                        "de esta transferencia. Acceso denegado."
                    ),
                    details={
                        "transfer_id": str(cmd.transfer_id),
                        "expected_company": str(transfer.destination_company_id),
                        "provided_company": str(cmd.receiver_company_id),
                    },
                )

            # ── 2.1. ANTI-FRAUDE: Segregación de Funciones (SoD) ──────────────────
            if transfer.created_by == cmd.received_by:
                logger.error(
                    f"[ICT][SECURITY] Intento de auto-recepción bloqueado. "
                    f"User={cmd.received_by} intentó recibir transfer={transfer.id}"
                )
                raise BusinessRuleException(
                    message="ERR_SELF_RECEIPT_NOT_ALLOWED: Por seguridad, "
                            "un traspaso no puede ser recibido por el mismo usuario que lo inició.",
                    details={"transfer_id": str(cmd.transfer_id), "user_id": str(cmd.received_by)}
                )

            # ── 3. Validar estado del documento ───────────────────────────────────
            if transfer.status == TransferStatus.DELIVERED:
                raise ConflictException(f"ERR_ALREADY_RECEIVED: La transferencia {transfer.folio} ya fue recibida.")

            if transfer.status == TransferStatus.CANCELLED:
                raise BusinessRuleException(f"ERR_CANCELLED_TRANSFER: La transferencia {transfer.folio} fue cancelada.")

            # ── 4. Determinar cantidad efectiva a recibir ──────────────────────────
            receive_qty_ok = cmd.received_quantity or transfer.quantity
            total_out_transit = receive_qty_ok + cmd.damaged_quantity

            if total_out_transit > transfer.quantity:
                raise BusinessRuleException(
                    message=f"ERR_QUANTITY_EXCESS: No se puede procesar más de lo despachado.",
                    details={"dispatched": str(transfer.quantity), "received_total": str(total_out_transit)}
                )

            # ── 5. Resolver WAC del tránsito ───────────────────────────────────────
            transit_product_id = transfer.destination_product_id or transfer.product_id
            try:
                val_transit = await self.repo.get_wac_valuation(
                    product_id=transit_product_id,
                    warehouse_id=transfer.transit_warehouse_id,
                    company_id=cmd.receiver_company_id,
                )
                transit_wac = val_transit.wac if val_transit else transfer.unit_price
            except Exception:
                transit_wac = transfer.unit_price

            # ── 5.1 ASYNC FAST-TRACK (Phase 61): Validation moved to Background Tasks ──
            # Skip synchronous check to return 202 Accepted faster.
            pass

            # ── 6. TRANSIT_RELEASE: Sacar del almacén lógico de tránsito ──────────
            release_movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transfer.transit_warehouse_id,
                product_id=transit_product_id,
                company_id=cmd.receiver_company_id,
                quantity=-total_out_transit,
                uom_id=transfer.uom_id,
                weight=transfer.weight,
                price=transit_wac,
                movement_type=MovementType.TRANSIT_RELEASE.value,
                document_type="ICT_TRANSIT_OUT",
                document_id=cmd.transfer_id,
            )
            await self.repo.record_movement(release_movement, allow_negative=True)

            # ── 7. TRANSFER_IN: Acreditar en almacén físico de Empresa B ──────────────
            sealed_transfer_price = transfer.unit_price
            acquisition_cost_b = Money(amount=(receive_qty_ok * sealed_transfer_price.amount).quantize(Decimal("0.0001")), currency=transfer.currency)

            in_movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transfer.destination_warehouse_id,
                product_id=transit_product_id,
                company_id=cmd.receiver_company_id,
                quantity=receive_qty_ok,
                uom_id=transfer.uom_id,
                weight=transfer.weight,
                price=sealed_transfer_price,
                movement_type=MovementType.TRANSFER_IN.value,
                document_type="ICT_RECEIVE",
                document_id=cmd.transfer_id,
                # FIFO compliance
                available_quantity=receive_qty_ok,
                location=cmd.destination_location, # Assign location to record
                customs_pedimento_id=cmd.customs_pedimento_id or transfer.customs_pedimento_id,
                # FAST-TRACK
                validation_status="PENDING"
            )
            await self.repo.record_movement(in_movement)

            # ── 8. Actualizar documento de transferencia ───────────────────────────
            transfer.status = TransferStatus.DELIVERED
            transfer.received_at = datetime.now(timezone.utc)
            transfer.received_by = cmd.received_by
            transfer.received_quantity = receive_qty_ok
            transfer.damaged_quantity = cmd.damaged_quantity
            transfer.receive_movement_id = in_movement.id
            transfer.cost_b = acquisition_cost_b
            if cmd.notes:
                transfer.notes = (transfer.notes or "") + f"\n[RECEPCIÓN] {cmd.notes}"

            self.session.add(transfer)
            
            # ── 9. Actualizar Documento Espejo (PROCESSED) ─────────────────────────
            if transfer.mirror_document_id:
                mirror_stmt = select(InventoryDocument).where(InventoryDocument.id == transfer.mirror_document_id)
                mirror_res = await self.session.execute(mirror_stmt)
                mirror_doc = mirror_res.scalar_one_or_none()
                if mirror_doc:
                    mirror_doc.status = DocumentStatus.PROCESSED
                    mirror_doc.total_amount = acquisition_cost_b
                    self.session.add(mirror_doc)

            # ── 10. Publicar Evento de Dominio ─────────────────────────────────────
            publisher = EventPublisher()
            await publisher.publish("TransferCompletedEvent", {
                "transfer_id": str(transfer.id),
                "folio": transfer.folio,
                "received_qty": str(receive_qty_ok)
            })

            await AuditService.log_action(
                db=self.session,
                action="RECEIVING_ICT",
                user_id=cmd.received_by,
                entity_name="InterCompanyTransfer",
                entity_id=str(transfer.id),
                details=str({"folio": transfer.folio, "qty": str(receive_qty_ok)})
            )
            
            await self.session.flush()

        return self._to_document_entity(transfer)

    # ═══════════════════════════════════════════════════════════════════════════
    # COMANDO 3: CancelTransfer (Empresa A)
    # ═══════════════════════════════════════════════════════════════════════════

    async def cancel_transfer(
        self, cmd: CancelTransferCommand
    ) -> TransferDocumentEntity:
        """
        Cancela una transferencia que aún no ha sido recibida.
        Revierte los movimientos: devuelve el stock del tránsito al almacén de A.
        """
        async with self.session.begin():
            logger.info(
                f"[ICT] CancelTransfer Transaction: transfer_id={cmd.transfer_id} | "
                f"Requester={cmd.requester_company_id}"
            )

            stmt = select(InterCompanyTransfer).where(
                InterCompanyTransfer.id == cmd.transfer_id
            )
            result = await self.session.execute(stmt)
            transfer = result.scalar_one_or_none()

            if not transfer:
                raise NotFoundException(f"ERR_TRANSFER_NOT_FOUND: Transfer {cmd.transfer_id} no existe.")

            # ── 1. Seguridad y Estado ─────────────────────────────────────────────
            if transfer.company_id != cmd.requester_company_id:
                raise UnauthorizedException("ERR_CANCEL_UNAUTHORIZED: Solo el originador puede cancelar.")

            if transfer.status == TransferStatus.DELIVERED:
                raise ConflictException("ERR_ALREADY_DELIVERED: No se puede cancelar una entrega realizada.")

            if transfer.status == TransferStatus.CANCELLED:
                return self._to_document_entity(transfer) # Idempotencia

            # ── 2. RESTAURACIÓN FIFO (Legal Compliance) ──────────────────────────
            # Revertimos el consumo de saldo de todos los movimientos de salida vinculados
            stmt_outs = select(Movement).where(
                and_(
                    Movement.document_id == transfer.id,
                    Movement.movement_type == MovementType.TRANSFER_OUT.value
                )
            )
            res_outs = await self.session.execute(stmt_outs)
            out_movements = res_outs.scalars().all()
            
            for m in out_movements:
                if m.source_movement_id:
                    # RESTAURAR SALDO en la capa (layer) original
                    stmt_restore = (
                        sa.update(Movement)
                        .where(Movement.id == m.source_movement_id)
                        .values(available_quantity=Movement.available_quantity + abs(m.quantity))
                    )
                    await self.session.execute(stmt_restore)
                    logger.info(f"[FIFO] Saldo restaurado en origen: {m.source_movement_id} (+{abs(m.quantity)})")

            # ── 3. Contra-asiento: TRANSIT_RELEASE (sacar de hold de B) ──────────
            transit_product_id = transfer.destination_product_id or transfer.product_id
            cancel_transit = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transfer.transit_warehouse_id,
                product_id=transit_product_id,
                company_id=transfer.destination_company_id,
                quantity=-transfer.quantity,
                uom_id=transfer.uom_id,
                weight=transfer.weight,
                price=transfer.unit_price if transfer.unit_price else Money(Decimal("0.0"), transfer.currency),
                movement_type=MovementType.TRANSIT_RELEASE.value,
                document_type="ICT_CANCEL_TRANSIT",
                document_id=cmd.transfer_id,
            )
            await self.repo.record_movement(cancel_transit, allow_negative=True)

            # ── 4. TRANSFER_IN: Regresar al almacén físico de Empresa A ────────
            # REGISTRAR DEVOLUCIÓN: available_quantity=0 para no duplicar saldo (ya restaurado arriba)
            restore_movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transfer.origin_warehouse_id,
                product_id=transfer.product_id,
                company_id=transfer.company_id,
                quantity=transfer.quantity,
                uom_id=transfer.uom_id,
                weight=transfer.weight,
                price=transfer.unit_price if transfer.unit_price else Money(Decimal("0.0"), transfer.currency),
                movement_type=MovementType.TRANSFER_IN.value,
                document_type="ICT_CANCEL_RETURN",
                document_id=cmd.transfer_id,
                available_quantity=Decimal("0.0") 
            )
            await self.repo.record_movement(restore_movement)

            # ── 5. Actualizar Documentos ──────────────────────────────────────────
            transfer.status = TransferStatus.CANCELLED
            transfer.notes = (transfer.notes or "") + f"\n[CANCELACIÓN] {cmd.reason or 'Sin motivo.'}"
            self.session.add(transfer)
            
            if transfer.mirror_document_id:
                mirror_stmt = select(InventoryDocument).where(InventoryDocument.id == transfer.mirror_document_id)
                mirror_res = await self.session.execute(mirror_stmt)
                mirror_doc = mirror_res.scalar_one_or_none()
                if mirror_doc:
                    mirror_doc.status = DocumentStatus.CANCELLED
                    self.session.add(mirror_doc)

            await AuditService.log_action(
                db=self.session,
                action="CANCEL_INTER_COMPANY_TRANSFER",
                user_id=cmd.requester_id,
                entity_name="InterCompanyTransfer",
                entity_id=str(transfer.id),
                details=str({"folio": transfer.folio, "reason": cmd.reason})
            )
            
            await self.session.flush()

        return self._to_document_entity(transfer)

    # ═══════════════════════════════════════════════════════════════════════════
    # COMANDO 4: RevertTransfer (Empresa A — Reclamación de Orphaned Transfer)
    # ═══════════════════════════════════════════════════════════════════════════

        async with self.session.begin():
            logger.info(
                f"[ICT] RevertTransfer Transaction: transfer_id={cmd.transfer_id} | "
                f"Requester={cmd.requester_company_id}"
            )

            stmt = select(InterCompanyTransfer).where(InterCompanyTransfer.id == cmd.transfer_id)
            result = await self.session.execute(stmt)
            transfer = result.scalar_one_or_none()

            if not transfer:
                raise NotFoundException(f"ERR_TRANSFER_NOT_FOUND: Transfer {cmd.transfer_id} no existe.")

            if transfer.company_id != cmd.requester_company_id:
                raise UnauthorizedException("ERR_REVERT_UNAUTHORIZED: Solo el originador puede reclamar el stock huérfano.")

            if transfer.status == TransferStatus.DELIVERED:
                raise ConflictException("ERR_ALREADY_DELIVERED: No se puede revertir una transferencia ya entregada.")
            if transfer.status == TransferStatus.CANCELLED:
                return self._to_document_entity(transfer)

            # ── 1. RESTAURACIÓN FIFO (Legal Restoral) ─────────────────────────────
            stmt_outs = select(Movement).where(
                and_(
                    Movement.document_id == transfer.id,
                    Movement.movement_type == MovementType.TRANSFER_OUT.value
                )
            )
            res_outs = await self.session.execute(stmt_outs)
            out_movements = res_outs.scalars().all()
            
            for m in out_movements:
                if m.source_movement_id:
                    # RESTAURAR SALDO en la capa origen
                    stmt_restore = (
                        sa.update(Movement)
                        .where(Movement.id == m.source_movement_id)
                        .values(available_quantity=Movement.available_quantity + abs(m.quantity))
                    )
                    await self.session.execute(stmt_restore)

            # ── 2. Cancelar Documento Espejo (DRAFT) de Empresa B ─────────────────────
            if transfer.mirror_document_id:
                mirror_stmt = select(InventoryDocument).where(InventoryDocument.id == transfer.mirror_document_id)
                mirror_res = await self.session.execute(mirror_stmt)
                mirror_doc = mirror_res.scalar_one_or_none()
                if mirror_doc:
                    mirror_doc.status = DocumentStatus.CANCELLED
                    self.session.add(mirror_doc)

            # ── 3. Contra-asiento: TRANSIT_RELEASE (sacar del hold de B) ──────────
            transit_product_id = transfer.destination_product_id or transfer.product_id
            sealed_price = transfer.unit_price if transfer.unit_price else Money(Decimal("0.0"), transfer.currency)

            cancel_transit = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transfer.transit_warehouse_id,
                product_id=transit_product_id,
                company_id=transfer.destination_company_id,
                quantity=-transfer.quantity,
                uom_id=transfer.uom_id,
                weight=transfer.weight,
                price=sealed_price,
                movement_type=MovementType.TRANSIT_RELEASE.value,
                document_type="ICT_REVERT_TRANSIT",
                document_id=cmd.transfer_id,
                comments="Reclamación de Transferencia No Entregada",
            )
            await self.repo.record_movement(cancel_transit, allow_negative=True)

            # ── 4. TRANSFER_IN: Devolver al almacén físico de Empresa A ────────
            restore_movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=transfer.origin_warehouse_id,
                product_id=transfer.product_id,
                company_id=transfer.company_id,
                quantity=transfer.quantity,
                uom_id=transfer.uom_id,
                weight=transfer.weight,
                price=sealed_price,
                movement_type=MovementType.TRANSFER_IN.value,
                document_type="ICT_REVERT_RETURN",
                document_id=cmd.transfer_id,
                comments="Reclamación de Transferencia No Entregada",
                # Compliance: Saldo 0 porque restauramos el original
                available_quantity=Decimal("0.0")
            )
            await self.repo.record_movement(restore_movement)

            # ── 5. Cerrar documento ICT ──────────────────────────────────────
            transfer.status = TransferStatus.CANCELLED
            transfer.notes = (transfer.notes or "") + (
                f"\n[REVERSIÓN] Reclamado por Empresa A. Motivo: {cmd.reason or 'Expiración/Abandonado'}"
            )
            self.session.add(transfer)

            await AuditService.log_action(
                db=self.session,
                action="REVERT_INTER_COMPANY_TRANSFER",
                user_id=getattr(cmd, "requester_id", getattr(cmd, "requested_by", None)),
                entity_name="InterCompanyTransfer",
                entity_id=str(transfer.id),
                details=str({"folio": transfer.folio, "reason": cmd.reason})
            )
            
            await self.session.flush()

        logger.info(f"[ICT] Transfer REVERTED (Orphan reclaimed): folio={transfer.folio}")
        return self._to_document_entity(transfer)

    # ═══════════════════════════════════════════════════════════════════════════

    async def get_transfer_by_id(
        self, transfer_id: uuid.UUID, requester_company_id: uuid.UUID
    ) -> TransferDocumentEntity:
        """
        Recupera un documento de tránsito por su ID único.
        Ambas empresas (A y B) pueden consultar el documento si están involucradas.
        """
        stmt = select(InterCompanyTransfer).where(
            InterCompanyTransfer.id == transfer_id
        )
        result = await self.session.execute(stmt)
        transfer = result.scalar_one_or_none()

        if not transfer:
            raise NotFoundException(
                message=f"ERR_TRANSFER_NOT_FOUND: Transfer {transfer_id} no existe.",
                details={"transfer_id": str(transfer_id)},
            )

        # Validar acceso: debe ser Empresa A o Empresa B
        if (
            transfer.company_id != requester_company_id
            and transfer.destination_company_id != requester_company_id
        ):
            raise UnauthorizedException(
                message="ERR_TRANSFER_ACCESS_DENIED: No pertenece a esta transferencia.",
                details={"transfer_id": str(transfer_id)},
            )

        return self._to_document_entity(transfer)

    async def get_transfer_by_folio(
        self, folio: str, requester_company_id: uuid.UUID
    ) -> TransferDocumentEntity:
        """
        Recupera un documento de tránsito por su número de folio (útil para escaneos).
        Limitado a las empresas involucradas en la transferencia.
        """
        stmt = select(InterCompanyTransfer).where(
            InterCompanyTransfer.folio == folio
        )
        result = await self.session.execute(stmt)
        transfer = result.scalar_one_or_none()

        if not transfer:
            raise NotFoundException(
                message=f"ERR_TRANSFER_NOT_FOUND: No existe transferencia con el folio {folio}.",
                details={"folio": folio},
            )

        # Validar acceso
        logger.info(f"[ICT-DEBUG] Folio: {folio}")
        logger.info(f"[ICT-DEBUG] DB Origin Co: {transfer.company_id} (Type: {type(transfer.company_id)})")
        logger.info(f"[ICT-DEBUG] DB Dest Co:   {transfer.destination_company_id}")
        logger.info(f"[ICT-DEBUG] Requester Co: {requester_company_id} (Type: {type(requester_company_id)})")

        if (
            str(transfer.company_id) != str(requester_company_id)
            and str(transfer.destination_company_id) != str(requester_company_id)
        ):
            logger.warning(f"[ICT-DEBUG] ACCESS DENIED triggered for {folio}")
            raise UnauthorizedException(
                message="ERR_TRANSFER_ACCESS_DENIED: No tiene permiso para ver este folio.",
                details={"folio": folio},
            )

        return self._to_document_entity(transfer)

    async def list_pending_for_company_b(
        self, company_b_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[PendingTransferEntity]:
        """
        Lista todas las transferencias pendientes de recepción para la Empresa B.
        Solo expone documentos en estado SHIPPED dirigidos a esta empresa.
        """
        stmt = (
            select(InterCompanyTransfer)
            .where(
                and_(
                    InterCompanyTransfer.destination_company_id == company_b_id,
                    InterCompanyTransfer.status == TransferStatus.SHIPPED,
                )
            )
            .order_by(InterCompanyTransfer.shipped_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        transfers = result.scalars().all()

        return [
            PendingTransferEntity(
                id=t.id,
                folio=t.folio,
                status=TransferStatusEnum(t.status.value),
                origin_company_id=t.company_id,
                product_id=t.product_id,
                quantity=t.quantity,
                weight=t.weight,
                shipped_at=t.shipped_at,
                external_reference=t.external_reference,
                notes=t.notes,
                origin_sku=t.origin_sku,
                destination_sku=t.destination_sku,
            )
            for t in transfers
        ]

    async def list_outbound_for_company_a(
        self, company_a_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[TransferDocumentEntity]:
        """
        Lista todas las transferencias enviadas por la Empresa A.
        """
        stmt = (
            select(InterCompanyTransfer)
            .where(InterCompanyTransfer.company_id == company_a_id)
            .order_by(InterCompanyTransfer.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        transfers = result.scalars().all()
        return [self._to_document_entity(t) for t in transfers]

    # ═══════════════════════════════════════════════════════════════════════════
    # MAPPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def _to_document_entity(self, t: InterCompanyTransfer) -> TransferDocumentEntity:
        """
        Mapea el ORM a la entidad de respuesta API.
        Incluye el bloque financiero completo:
          - unit_price_at_dispatch: precio pactado (sellado)
          - wac_at_dispatch:        costo real de A
          - transfer_revenue_a:     ingreso de A (calculado al despacho)
          - acquisition_cost_b:     costo de B (calculado al recibir)
          - transfer_margin_a:      margen bruto de A (dinámico)
        """
        # Calcular margen dinámico (sólo disponible si tenemos ambos valores)
        transfer_margin_a: Optional[Money] = None
        if t.revenue_a and t.wac_origin:
            wac_cost_a = (t.quantity * t.wac_origin.amount).quantize(Decimal("0.0001"))
            margin_val = (t.revenue_a.amount - wac_cost_a).quantize(Decimal("0.0001"))
            transfer_margin_a = Money(amount=margin_val, currency=t.currency)

        return TransferDocumentEntity(
            id=t.id,
            folio=t.folio,
            status=TransferStatusEnum(t.status.value),
            origin=TransferPartyEntity(
                company_id=t.company_id,
                warehouse_id=t.origin_warehouse_id,
                sku=t.origin_sku,
                product_id=t.product_id,
            ),
            destination=TransferPartyEntity(
                company_id=t.destination_company_id,
                warehouse_id=t.destination_warehouse_id,
                sku=t.destination_sku,
                product_id=t.destination_product_id or t.product_id,
            ),
            product_id=t.product_id,
            uom_id=t.uom_id,
            quantity=t.quantity,
            weight=t.weight,
            currency=t.currency,
            # ── Bloque financiero (Money VO) ────
            unit_price_at_dispatch=t.unit_price,
            wac_at_dispatch=t.wac_origin,
            transfer_revenue_a=t.revenue_a,
            acquisition_cost_b=t.cost_b,
            transfer_margin_a=transfer_margin_a,
            # price_source y transfer_price_warning se inyectan en initiate si aplica
            # ────────────────────────
            received_quantity=t.received_quantity,
            notes=t.notes,
            external_reference=t.external_reference,
            # Phase 40: Compliance & Audit
            pending_financial_valuation=t.pending_financial_valuation,
            audit_notes=t.audit_notes,
            exchange_rate_dof=t.exchange_rate_dof,
            customs_pedimento=t.customs_pedimento,
            customs_pedimento_id=t.customs_pedimento_id,
            customs_doc_type=t.customs_doc_type,
            # Trazabilidad
            dispatch_movement_id=t.dispatch_movement_id,
            receive_movement_id=t.receive_movement_id,
            created_at=t.created_at,
            shipped_at=t.shipped_at,
            received_at=t.received_at
        )

    async def verify_density_and_compliance(self, movement_id: uuid.UUID, warehouse_id: uuid.UUID, location_code: str, quantity: Decimal, company_id: uuid.UUID):
        """
        [Phase 63] Industrial Async Reconciliation: Post-receive physical capacity validation.
        Leverages Master Data SSOT to detect compliance violations in background.
        """
        try:
            # 1. Physical Capacity Check via SSOT Client
            try:
                await self._check_location_capacity(warehouse_id, location_code, quantity, company_id)
                status = "CLEAN"
            except BusinessRuleException as be:
                logger.error(f"Post-Receive Density Guard Violation: {be.message}")
                status = "OVERFLOW_ALERT"
                # Note: Notification is already dispatched inside _check_location_capacity
            # 2. Update movement status atomically
            stmt = (
                update(Movement)
                .where(Movement.id == movement_id)
                .values(validation_status=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            
            # 3. Final Reconciliation Event
            publisher = EventPublisher()
            await publisher.publish("TransferValidationCompleted", {
                "movement_id": str(movement_id),
                "status": status
            })

            logger.info(f"✅ ASYNC_VAL_FINISH: Movement {movement_id} processed as {status}.")
            
        except Exception as e:
            logger.error(f"Critical error in verify_density_and_compliance: {str(e)}")
            await self.session.rollback()
