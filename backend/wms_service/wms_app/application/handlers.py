import uuid
from datetime import datetime
from typing import List, Optional, Any
from decimal import Decimal
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError

from common.exceptions import BusinessRuleException, NotFoundException
from wms_app.models import InventoryDocument, InventoryMovement, InventorySnapshot, DocumentStatus
from wms_app.models.sales_order import SalesOrder, SalesOrderStatus
from wms_app.models.concept import Concept, ConceptType
from wms_app.application.commands import (
    CreateInventoryDocumentCommand, 
    AddMovementCommand, 
    ConfirmDocumentCommand,
    CreateSalesOrderCommand,
    DispatchSalesOrderCommand
)
from wms_app.infrastructure.inventory_client import InventoryClient
from wms_app.infrastructure.tickets_client import TicketsClient

logger = logging.getLogger(__name__)

class BaseHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

class CreateInventoryDocumentHandler(BaseHandler):
    async def handle(self, command: CreateInventoryDocumentCommand, company_id: uuid.UUID) -> Any:
        # Business Rule: Check if folio already exists for this tenant
        stmt = select(InventoryDocument).filter_by(
            company_id=company_id, 
            folio=command.folio
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise BusinessRuleException(f"Document with folio {command.folio} already exists.")

        # Obtener el siguiente número de secuencia para la compañía
        stmt_seq = select(InventoryDocument.sequence_number).filter_by(company_id=company_id).order_by(InventoryDocument.sequence_number.desc()).limit(1)
        res_seq = await self.session.execute(stmt_seq)
        last_seq = res_seq.scalar_one_or_none()
        next_seq = (last_seq + 1) if last_seq is not None else 1

        doc = InventoryDocument(
            company_id=company_id,
            sequence_number=next_seq,
            folio=command.folio,
            warehouse_id=uuid.UUID(command.warehouse_id),
            concept_id=uuid.UUID(command.concept_id),
            target_company_id=uuid.UUID(command.target_company_id) if command.target_company_id else None,
            target_warehouse_id=uuid.UUID(command.target_warehouse_id) if command.target_warehouse_id else None,
            status=DocumentStatus.DRAFT,
            date=datetime.utcnow()
        )
        self.session.add(doc)
        await self.session.flush() # Populate ID
        return doc

class AddMovementHandler(BaseHandler):
    async def handle(self, command: AddMovementCommand, company_id: uuid.UUID) -> Any:
        # 1. Fetch Tenant Document
        stmt = select(InventoryDocument).filter_by(
            id=uuid.UUID(command.document_id), 
            company_id=company_id
        )
        result = await self.session.execute(stmt)
        doc = result.scalar_one_or_none()

        if not doc:
            raise NotFoundException(f"Document {command.document_id} not found.")

        # 2. Immutability Check
        if doc.status == DocumentStatus.CONFIRMED:
            raise BusinessRuleException("Cannot add movements to a CONFIRMED document.")

        # 3. Validation: Warehouse Match
        if uuid.UUID(command.warehouse_id) != doc.warehouse_id:
             raise BusinessRuleException("Movement warehouse must match document warehouse.")

        # Obtener el número de secuencia de la línea
        stmt_seq = select(InventoryMovement).filter_by(document_id=doc.id).order_by(InventoryMovement.sequence_number.desc())
        res_seq = await self.session.execute(stmt_seq)
        last_mov = res_seq.scalars().first()
        next_seq = (last_mov.sequence_number + 1) if last_mov else 1

        mov = InventoryMovement(
            company_id=company_id,
            document_id=doc.id,
            product_id=uuid.UUID(command.product_id),
            warehouse_id=uuid.UUID(command.warehouse_id),
            sequence_number=next_seq,
            quantity=Decimal(str(command.quantity)),
            purchase_price=Decimal(str(command.unit_cost)),
            location_id=uuid.UUID(command.location_id) if command.location_id else None,
            created_at=datetime.utcnow()
        )
        self.session.add(mov)
        await self.session.flush()
        return mov

class ConfirmDocumentHandler(BaseHandler):
    async def handle(self, command: ConfirmDocumentCommand, company_id: uuid.UUID) -> Any:
        # 1. Fetch Tenant Document
        stmt = select(InventoryDocument).filter_by(
            id=uuid.UUID(command.document_id),
            company_id=company_id
        ).with_for_update()
        
        result = await self.session.execute(stmt)
        doc = result.scalar_one_or_none()

        if not doc:
             raise NotFoundException(f"Document {command.document_id} not found.")

        if doc.status == DocumentStatus.CONFIRMED:
             return doc

        # 2. Fetch Concept for type validation
        stmt_concept = select(Concept).filter_by(id=doc.concept_id, company_id=company_id)
        res_concept = await self.session.execute(stmt_concept)
        concept = res_concept.scalar_one_or_none()

        if not concept:
            raise NotFoundException("Concept not found for document.")

        # 3. Process Movements & Update Snapshots
        stmt_movs = select(InventoryMovement).filter_by(
            document_id=doc.id, 
            company_id=company_id
        )
        res_movs = await self.session.execute(stmt_movs)
        movements = res_movs.scalars().all()

        # Mapping for Inventory Service
        inv_type_map = {
            ConceptType.ENTRY: "IN",
            ConceptType.OUTPUT: "OUT",
            ConceptType.ADJUSTMENT: "ADJUSTMENT",
            ConceptType.TRANSFER: "OUT" # A simple transfer document starts as an OUT from source
        }
        movement_type = inv_type_map.get(concept.concept_type, "ADJUSTMENT")

        for mov in movements:
            # A. Update local WMS Snapshot (Physical)
            if concept.affect_stock:
                await self._update_snapshot(mov, company_id)
            
            # B. Trigger Financial Record (Inventory Ledger)
            qty = float(mov.quantity)
            if movement_type == "OUT":
                qty = -qty # Negative for egression

            payload = {
                "warehouse_id": str(mov.warehouse_id),
                "product_id": str(mov.product_id),
                "quantity": qty,
                "movement_type": movement_type,
                "document_type": "WMS_DOCUMENT",
                "document_id": str(doc.id)
            }
            
            # Si falla, la transacci\u00f3n padre fallar\u00e1 (Atomicidad distribuida)
            await InventoryClient._post("/movements", payload)

        # 4. Change Status
        doc.status = DocumentStatus.CONFIRMED
        doc.updated_at = datetime.utcnow()
        
        # 5. [INTER-COMPANY] Create Mirror Document if TRANSFER
        if concept.concept_type == ConceptType.TRANSFER and doc.target_company_id:
            await self._create_mirror_entry_document(doc, movements)
            
        return doc

    async def _create_mirror_entry_document(self, source_doc: Any, movements: List[Any]):
        # Find a suitable 'Entry' concept for the target company
        stmt_target_concept = select(Concept).filter_by(
            company_id=source_doc.target_company_id,
            concept_type=ConceptType.ENTRY
        )
        res_target_concept = await self.session.execute(stmt_target_concept)
        target_concept = res_target_concept.scalar_one_or_none()

        if not target_concept:
             logger.warning(f"Target company {source_doc.target_company_id} has no Entry concept. Mirror skipped.")
             return

        mirror_doc = InventoryDocument(
            company_id=source_doc.target_company_id,
            folio=f"MIRROR-{source_doc.folio}",
            warehouse_id=source_doc.target_warehouse_id,
            concept_id=target_concept.id,
            status=DocumentStatus.DRAFT,
            reference=source_doc.folio,
            observations=f"Mirror of Transfer from Company {source_doc.company_id}",
            date=datetime.utcnow()
        )
        self.session.add(mirror_doc)
        await self.session.flush()

        for i, mov in enumerate(movements):
            mirror_mov = InventoryMovement(
                company_id=source_doc.target_company_id,
                document_id=mirror_doc.id,
                sequence_number=i + 1,
                product_id=mov.product_id,
                warehouse_id=source_doc.target_warehouse_id,
                quantity=mov.quantity,
                purchase_price=mov.purchase_price,
                created_at=datetime.utcnow()
            )
            self.session.add(mirror_mov)

    async def _update_snapshot(self, mov: Any, company_id: uuid.UUID):
        stmt = select(InventorySnapshot).filter_by(
            company_id=company_id,
            product_id=mov.product_id,
            warehouse_id=mov.warehouse_id
        ).with_for_update()
        
        result = await self.session.execute(stmt)
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            snapshot = InventorySnapshot(
                company_id=company_id,
                product_id=mov.product_id,
                warehouse_id=mov.warehouse_id,
                quantity_on_hand=Decimal("0.0"),
                average_cost=Decimal("0.0"),
                updated_at=datetime.utcnow()
            )
            self.session.add(snapshot)
        
        current_stock = snapshot.quantity_on_hand
        current_cost = snapshot.average_cost
        
        incoming_qty = mov.quantity
        incoming_cost = mov.purchase_price
        
        current_total_value = current_stock * current_cost
        incoming_value = incoming_qty * incoming_cost
        new_total_qty = current_stock + incoming_qty
        
        if new_total_qty != 0:
            new_avg_cost = (current_total_value + incoming_value) / new_total_qty
        else:
            new_avg_cost = Decimal("0.0")

        snapshot.quantity_on_hand = new_total_qty
        snapshot.average_cost = new_avg_cost
        snapshot.updated_at = datetime.utcnow()

class CreateSalesOrderHandler(BaseHandler):
    async def handle(self, command: CreateSalesOrderCommand, company_id: uuid.UUID) -> SalesOrder:
        """
        Crea una SalesOrder y descuenta stock atómicamente.
        Si el descuento de stock falla, la orden se cancela y se genera un ticket.
        """
        
        # 1. Crear Orden en DRAFT con datos completos
        order = SalesOrder(
            company_id=company_id,
            folio=command.folio,
            status=SalesOrderStatus.DRAFT,
            product_id=uuid.UUID(command.product_id),
            warehouse_id=uuid.UUID(command.warehouse_id),
            uom_id=uuid.UUID(command.uom_id),
            quantity=command.quantity,
            total_items=int(command.quantity),
            observations=command.comments
        )
        self.session.add(order)
        await self.session.flush() # Para tener el ID de la orden

        try:
            # 2. Intentar reservar stock (en lugar de descontar directamente)
            logger.info(f"[*] Attempting to reserve stock for order {order.folio}")
            await InventoryClient.reserve_stock(
                product_id=uuid.UUID(command.product_id),
                warehouse_id=uuid.UUID(command.warehouse_id),
                quantity=command.quantity,
                uom_id=uuid.UUID(command.uom_id),
                reference_id=order.id
            )
            
            # 3. Si tiene éxito, confirmar orden
            order.status = SalesOrderStatus.CONFIRMED
            logger.info(f"✅ Order {order.folio} confirmed and stock reserved.")

        except Exception as e:
            # 4. ROLLBACK LÓGICO
            logger.error(f"❌ Stock reduction failed for order {order.folio}: {str(e)}")
            order.status = SalesOrderStatus.CANCELLED
            
            # 5. Generar Ticket de Alerta (Tickets Service)
            try:
                await TicketsClient.create_stock_alert_ticket(
                    product_id=uuid.UUID(command.product_id),
                    warehouse_id=uuid.UUID(command.warehouse_id),
                    requested_qty=command.quantity,
                    company_id=company_id
                )
                logger.info("🎫 Stock alert ticket generated.")
            except Exception as ticket_err:
                logger.error(f"⚠️ Could not generate alert ticket: {ticket_err}")

            # Re-lanzar error para que el API devuelva el fallo, pero el cambio a CANCELLED se guarda
            # Nota: Al usar AsyncSession, si hacemos commit aquí, el cambio a CANCELLED persiste.
            # Si el API middleware hace rollback general, este cambio se perdería. 
            # Para asegurar persistencia del "Cancelado", podríamos necesitar un flush o commit parcial.
            await self.session.commit()
            raise BusinessRuleException(f"Order could not be confirmed: {str(e)}")

        await self.session.commit()
        return order

class DispatchSalesOrderHandler(BaseHandler):
    async def handle(self, command: DispatchSalesOrderCommand, company_id: uuid.UUID) -> Any:
        # 1. Recuperar la Orden
        stmt = select(SalesOrder).filter_by(id=uuid.UUID(command.sales_order_id), company_id=company_id).with_for_update()
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise NotFoundException("Sales Order not found.")

        if order.status != SalesOrderStatus.CONFIRMED:
            raise BusinessRuleException(f"Order must be CONFIRMED to dispatch. Current status: {order.status}")

        # 2. Registrar la salida real en el Servicio de Inventario (Fulfilling reservation)
        try:
            logger.info(f"[*] Dispatching order {order.folio}. Fulfilling reservation in Inventory Service.")
            await InventoryClient.decrease_stock(
                product_id=order.product_id,
                warehouse_id=uuid.UUID(command.warehouse_id),
                quantity=float(order.quantity),
                uom_id=order.uom_id,
                reference_id=order.id,
                comments=f"Despacho Venta Folio: {order.folio}",
                fulfill_reservation=True
            )
        except Exception as e:
            logger.error(f"❌ Dispatch failed for order {order.folio}: {str(e)}")
            raise BusinessRuleException(f"Dispatch failed: {str(e)}")

        # 3. Generar Documento de Inventario (Local WMS audit)
        # Buscamos concepto de salida por venta (ejm: SALIDA POR VENTA)
        # 🔒 SECURITY SHIELD: mandatory company_id filter
        stmt_concept = select(Concept).filter(
            Concept.company_id == company_id, 
            Concept.concept_type == ConceptType.OUTPUT
        ).limit(1)
        res_concept = await self.session.execute(stmt_concept)
        concept = res_concept.scalar_one_or_none()

        if concept:
            doc_handler = CreateInventoryDocumentHandler(self.session)
            doc_cmd = CreateInventoryDocumentCommand(
                folio=f"DISP-{order.folio}",
                company_id=str(company_id),
                warehouse_id=command.warehouse_id,
                concept_id=str(concept.id)
            )
            doc = await doc_handler.handle(doc_cmd, company_id)
            
            mov_handler = AddMovementHandler(self.session)
            mov_cmd = AddMovementCommand(
                document_id=str(doc.id),
                company_id=str(company_id),
                product_id=str(order.product_id),
                warehouse_id=command.warehouse_id,
                quantity=order.quantity,
                unit_cost=Decimal("0.0"), # Costo se resuelve en inventory_service
                location_id=command.location_id
            )
            await mov_handler.handle(mov_cmd, company_id)
            
            # Confirmamos el documento localmente (solo marca como confirmado, el client ya fue llamado arriba)
            doc.status = DocumentStatus.CONFIRMED
            doc.updated_at = datetime.utcnow()

        # 4. Actualizar Estado de la Orden
        order.status = SalesOrderStatus.SHIPPED
        order.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return order
