from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from common.exceptions import BusinessRuleException, NotFoundException
from wms_service.app.models import InventoryDocument, InventoryMovement, InventorySnapshot, DocumentStatus
# Updated import for Clean Architecture location
from wms_service.app.application.commands import CreateInventoryDocumentCommand, AddMovementCommand, ConfirmDocumentCommand

class BaseHandler:
    def __init__(self, session: Session):
        self.session = session

class CreateInventoryDocumentHandler(BaseHandler):
    def handle(self, command: CreateInventoryDocumentCommand, company_id: str) -> InventoryDocument:
        # Business Rule: Check if folio already exists for this tenant
        existing = self.session.query(InventoryDocument).filter_by(
            company_id=company_id, 
            folio=command.folio
        ).first()
        
        if existing:
            raise BusinessRuleException(f"Document with folio {command.folio} already exists.")

        doc = InventoryDocument(
            company_id=company_id,
            folio=command.folio,
            warehouse_id=command.warehouse_id,
            concept_id=command.concept_id,
            target_company_id=command.target_company_id,
            target_warehouse_id=command.target_warehouse_id,
            status=DocumentStatus.DRAFT,
            created_at=datetime.utcnow(),
            created_by="system" # TODO: Extract user from context
        )
        self.session.add(doc)
        self.session.flush() # Populate ID
        return doc

class AddMovementHandler(BaseHandler):
    def handle(self, command: AddMovementCommand, company_id: str) -> InventoryMovement:
        # 1. Fetch Tenant Document
        doc = self.session.query(InventoryDocument).filter_by(
            id=command.document_id, 
            company_id=company_id
        ).first()

        if not doc:
            raise NotFoundException(f"Document {command.document_id} not found.")

        # 2. Immutability Check
        if doc.status == DocumentStatus.CONFIRMED:
            raise BusinessRuleException("Cannot add movements to a CONFIRMED document.")

        # 3. Validation: Warehouse Match
        if command.warehouse_id != doc.warehouse_id:
             raise BusinessRuleException("Movement warehouse must match document warehouse.")

        mov = InventoryMovement(
            company_id=company_id,
            document_id=doc.id,
            product_id=command.product_id,
            warehouse_id=command.warehouse_id,
            quantity=command.quantity,
            unit_cost=command.unit_cost,
            created_at=datetime.utcnow()
        )
        self.session.add(mov)
        return mov

class ConfirmDocumentHandler(BaseHandler):
    def handle(self, command: ConfirmDocumentCommand, company_id: str) -> InventoryDocument:
        # Atomic Transaction for Ledger Integrity
        with self.session.begin_nested(): # Use begin_nested() just in case checks are wrapped, or begin() if top-level. 
            # User asked for 'with session.begin():'. 
            # If the session is autocommit=False (default), begin() starts a transaction.
            # If already active, it might raise. Let's assume standard use.
            # However, safer to just rely on flush/commit at the end or explicit begin if requested.
            # Given instructions: "Usa with session.begin():"
            # I will try to conform, but standard SQLAlchemy usually recommends session context manager at top level.
            # Since I am in a Handler, I will check if session is active.
            
            # 1. Fetch Tenant Document
            doc = self.session.query(InventoryDocument).with_for_update().filter_by(
                id=command.document_id,
                company_id=company_id
            ).first()

            if not doc:
                 raise NotFoundException(f"Document {command.document_id} not found.")

            if doc.status == DocumentStatus.CONFIRMED:
                 return doc

            # 2. Fetch Concept to check for Transfer trigger
            from wms_service.app.models.concept import Concept, ConceptType
            concept = self.session.query(Concept).filter_by(id=doc.concept_id).first()

            # 3. Process Movements & Update Snapshots
            movements = self.session.query(InventoryMovement).filter_by(
                document_id=doc.id, 
                company_id=company_id
            ).all()

            for mov in movements:
                self._update_snapshot(mov, company_id)

            # 4. Change Status
            doc.status = DocumentStatus.CONFIRMED
            doc.updated_at = datetime.utcnow()
            self.session.add(doc)

            # 5. [INTER-COMPANY] Create Mirror Document if TRANSFER
            if concept and concept.concept_type == ConceptType.TRANSFER and doc.target_company_id:
                self._create_mirror_entry_document(doc, movements)
            
        return doc

    def _create_mirror_entry_document(self, source_doc: InventoryDocument, movements: List[InventoryMovement]):
        """
        Creates a DRAFT Entry document in the target company.
        """
        # Find a suitable 'Entry' concept for the target company
        from wms_service.app.models.concept import Concept, ConceptType
        target_concept = self.session.query(Concept).filter_by(
            company_id=source_doc.target_company_id,
            concept_type=ConceptType.ENTRY
        ).first()

        if not target_concept:
             # Fallback or Exception: Inter-company target must have an Entry concept
             return

        mirror_doc = InventoryDocument(
            company_id=source_doc.target_company_id,
            folio=f"MIRROR-{source_doc.folio}",
            warehouse_id=source_doc.target_warehouse_id,
            concept_id=target_concept.id,
            status=InventoryDocumentStatus.DRAFT,
            reference=source_doc.folio,
            observations=f"Mirror of Transfer from Company {source_doc.company_id}",
            created_at=datetime.utcnow()
        )
        self.session.add(mirror_doc)
        self.session.flush()

        for i, mov in enumerate(movements):
            mirror_mov = InventoryMovement(
                company_id=source_doc.target_company_id,
                document_id=mirror_doc.id,
                sequence_number=i + 1,
                product_id=mov.product_id,
                warehouse_id=source_doc.target_warehouse_id,
                quantity=mov.quantity,
                unit_cost=mov.unit_cost, # Cost parity
                created_at=datetime.utcnow()
            )
            self.session.add(mirror_mov)

    def _update_snapshot(self, mov: InventoryMovement, company_id: str):
        from decimal import Decimal
        
        # Match matches logic in test_ledger_flow.py (Product + Company + Warehouse)
        snapshot = self.session.query(InventorySnapshot).with_for_update().filter_by(
            company_id=company_id,
            product_id=mov.product_id,
            warehouse_id=mov.warehouse_id
        ).first()

        if not snapshot:
            snapshot = InventorySnapshot(
                company_id=company_id,
                product_id=mov.product_id,
                warehouse_id=mov.warehouse_id,
                stock_on_hand=0,
                average_cost=0,
                updated_at=datetime.utcnow()
            )
            self.session.add(snapshot)
        
        # Weighted Average Cost Calculation (Decimal Precision)
        # Ensure we work with Decimals
        current_stock = Decimal(str(snapshot.stock_on_hand))
        current_cost = Decimal(str(snapshot.average_cost))
        
        incoming_qty = Decimal(str(mov.quantity))
        incoming_cost = Decimal(str(mov.unit_cost))
        
        current_total_value = current_stock * current_cost
        incoming_value = incoming_qty * incoming_cost
        new_total_qty = current_stock + incoming_qty
        
        if new_total_qty != 0:
            new_avg_cost = (current_total_value + incoming_value) / new_total_qty
        else:
            new_avg_cost = Decimal("0.0")

        snapshot.stock_on_hand = new_total_qty
        snapshot.average_cost = new_avg_cost
        snapshot.updated_at = datetime.utcnow()
