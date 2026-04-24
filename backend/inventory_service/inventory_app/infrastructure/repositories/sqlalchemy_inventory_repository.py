from datetime import datetime, timedelta
from typing import List, Optional, Any
import logging
import uuid
import asyncio
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, text, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.domain.entities.inventory_item import (
    InventoryLevelEntity, 
    InventoryTransactionEntity,
    MovementEntity,
    MovementSummaryEntity,
    DocumentListRowEntity,
    KardexRowEntity,
    WACValuationEntity,
    RotationABCEntity,
    InventorySearchRowEntity,
    DashboardTelemetryEntity,
    StockAlertEntity,
    HourlyMovementEntity,
    DocumentDetailEntity,
    DocumentItemEntity
)
from inventory_app.models.item_variant import ItemVariant
from inventory_app.models.inventory import InventoryLevel, InventoryTransaction
from inventory_app.models.movement import Movement
from inventory_app.models.document import InventoryDocument, DocumentStatus
from inventory_app.infrastructure.tickets_client import TicketsClient
from common.exceptions import UnauthorizedException
from common.audit.logger import AuditLogger
from inventory_app.models.warehouse import Warehouse
from inventory_app.models.inter_company_transfer import InterCompanyTransfer
from inventory_app.models.customs_pedimento import CustomsPedimento
from inventory_app.models.location import InventoryLocation
from inventory_app.domain.interfaces.master_data_client import IMasterDataClient
from common.domain.value_objects import Money

logger = logging.getLogger(__name__)

class SQLAlchemyInventoryRepository(IInventoryRepository):
    def __init__(self, session: AsyncSession, md_client: Optional[IMasterDataClient] = None):
        self.session = session
        self.md_client = md_client

    async def _validate_warehouse_ownership(self, warehouse_id: uuid.UUID, company_id: uuid.UUID):
        """
        [ZERO ZERO TRUST] Validates that the warehouse belongs to the current company.
        Gracefully handles non-UUID strings (e.g. mocks) to avoid db errors.
        """
        # 1. Forensic Guard: If it's a string, try to parse it. If it fails, it's not a real DB warehouse.
        target_id = warehouse_id
        if isinstance(warehouse_id, str):
            try:
                target_id = uuid.UUID(warehouse_id)
            except ValueError:
                # If it's a mock string like 'WH-TIJ-01', it won't be in the DB anyway.
                # In demo mode, we might want to bypass this, but for zero-trust we fail.
                # However, to avoid blocking the user's manual "mock" usage, we log as warning.
                logger.warning(f"WAREHOUSE_MOCK_DETECTED: {warehouse_id} is not a valid UUID. Blocking for integrity.")
                raise UnauthorizedException(message=f"ERR_INVALID_WAREHOUSE_FORMAT: {warehouse_id}")

        # 2. Forensic Guard: Ensure company_id is a UUID object
        strict_company_id = company_id
        if isinstance(company_id, str):
            try:
                strict_company_id = uuid.UUID(company_id)
            except:
                pass

        stmt = select(Warehouse).where(Warehouse.id == target_id, Warehouse.company_id == strict_company_id)
        result = await self.session.execute(stmt)
        warehouse = result.scalar_one_or_none()
        
        if not warehouse:
            # --- SELF-HEALING: Try to recover from Master Data ---
            if self.md_client:
                logger.info(f"[SELF-HEALING] Warehouse {target_id} not found in local cache. Fetching from Master Data...")
                try:
                    md_wh = await self.md_client.get_warehouse(target_id, strict_company_id)
                    if md_wh:
                        # Auto-sync: Create local shadow copy
                        new_wh = Warehouse(
                            id=target_id,
                            company_id=strict_company_id,
                            tenant_id=strict_company_id,
                            code=md_wh.get("code") or "SYNC",
                            name=md_wh.get("name") or "Synchronized Warehouse",
                            location=md_wh.get("location")
                        )
                        # Triple-Check Assignment
                        new_wh.tenant_id = strict_company_id
                        new_wh.company_id = strict_company_id
                        
                        self.session.add(new_wh)
                        await self.session.flush() # Force ID presence for following operations
                        logger.info(f"[SELF-HEALING] Synchronized warehouse {target_id} (Tenant: {strict_company_id}) from Master Data.")
                        return # Success
                except Exception as e:
                    logger.error(f"[SELF-HEALING] Failed to recover warehouse {target_id}: {str(e)}")

            # Log suspicious attempt if still not found
            await AuditLogger.log_action(
                db=self.session,
                action="UNAUTHORIZED_WAREHOUSE_ACCESS",
                table_name="inventory_warehouses",
                record_id=str(warehouse_id),
                new_value={"denied_to_company": str(company_id)}
            )
            # Flush log before raising
            await self.session.flush()
            raise UnauthorizedException(
                message=f"ERR_WAREHOUSE_ACCESS_DENIED: Warehouse {warehouse_id} does not belong to Company {company_id}."
            )

    def _to_level_entity(self, stock_model: InventoryLevel) -> InventoryLevelEntity:
        return InventoryLevelEntity(
            warehouse_id=stock_model.warehouse_id,
            product_id=stock_model.product_id,
            uom_id=stock_model.uom_id,
            quantity=stock_model.quantity,
            reserved_quantity=stock_model.reserved_quantity,
            wac=stock_model.wac,
            last_price=stock_model.last_price,
            replacement_price=stock_model.replacement_price,
            company_id=stock_model.company_id
        )

    async def get_inventory_levels(self, company_id: uuid.UUID) -> List[InventoryLevelEntity]:
        stmt = select(InventoryLevel).where(InventoryLevel.company_id == company_id)
        result = await self.session.execute(stmt)
        return [self._to_level_entity(s) for s in result.scalars().all()]

    async def list_warehouses(self, company_id: uuid.UUID) -> List[Warehouse]:
        """Obtiene la lista de almacenes registrados para el tenant."""
        stmt = select(Warehouse).where(Warehouse.company_id == company_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_stock(self, warehouse_id: uuid.UUID, product_id: uuid.UUID, company_id: uuid.UUID) -> Optional[InventoryLevelEntity]:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        stmt = select(InventoryLevel).filter_by(
            warehouse_id=warehouse_id,
            product_id=product_id,
            company_id=company_id
        )
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()
        return self._to_level_entity(stock) if stock else None

    async def record_movement(self, movement: MovementEntity, allow_negative: bool = False, from_reservation: bool = False, client_request_id: Optional[str] = None) -> InventoryLevelEntity:
        # Forensic Guard: Ensure company_id is a UUID object
        strict_company_id = movement.company_id
        if isinstance(strict_company_id, str):
            try:
                strict_company_id = uuid.UUID(strict_company_id)
            except:
                pass

        if client_request_id:
            from common.models.idempotency_key import IdempotencyKey
            from sqlalchemy.exc import IntegrityError
            from common.exceptions import BusinessRuleException
            try:
                self.session.add(IdempotencyKey(key=client_request_id))
                await self.session.flush()
            except IntegrityError:
                raise ValueError("ERR_DUPLICATE_REQUEST: Idempotency conflict. Transaction already processed.")

        await self._validate_warehouse_ownership(movement.warehouse_id, movement.company_id)
        stmt = select(InventoryLevel).filter_by(
            warehouse_id=movement.warehouse_id,
            product_id=movement.product_id,
            company_id=movement.company_id
        )
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()
        
        if not stock:
            stock = InventoryLevel(
                warehouse_id=movement.warehouse_id,
                product_id=movement.product_id,
                company_id=strict_company_id,
                tenant_id=strict_company_id, # Simplified Multi-tenancy
                uom_id=movement.uom_id,
                quantity=Decimal(0),
                wac=Money(Decimal(0), "MXN"),
                last_price=Money(Decimal(0), "MXN"),
                replacement_price=Money(Decimal(0), "MXN")
            )
            self.session.add(stock)

        new_quantity = stock.quantity + movement.quantity
        if new_quantity < 0 and not allow_negative:
            raise ValueError("ERR_INSUFFICIENT_STOCK: Transaction aborted.")

        # ─── WAC Recalculation (Phase 33.5) ───
        # Only recalculate on IN movements with a positive price.
        if movement.movement_type == "IN" and movement.price and movement.price.amount > 0:
            current_qty = stock.quantity
            incoming_qty = movement.quantity
            incoming_price = movement.price.amount
            current_wac = stock.wac.amount if stock.wac else Decimal(0)

            if current_qty > 0:
                total_value = (current_qty * current_wac) + (incoming_qty * incoming_price)
                new_wac_amount = total_value / (current_qty + incoming_qty)
            else:
                new_wac_amount = incoming_price
            
            stock.wac = Money(amount=new_wac_amount.quantize(Decimal("0.0001")), currency=movement.price.currency)
            stock.last_price = movement.price

        stock.quantity = new_quantity
        
        if from_reservation:
            stock.reserved_quantity += movement.quantity 
            if stock.reserved_quantity < 0:
                stock.reserved_quantity = Decimal(0)

        # Create movement model
        movement_model = Movement(
            id=movement.id,
            warehouse_id=movement.warehouse_id,
            product_id=movement.product_id,
            company_id=movement.company_id,
            tenant_id=movement.company_id, # Simplified Multi-tenancy
            quantity=movement.quantity,
            uom_id=movement.uom_id,
            weight=movement.weight,
            price=movement.price,
            movement_type=movement.movement_type,
            document_type=movement.document_type,
            document_id=movement.document_id,
            concept_id=movement.concept_id,
            comments=getattr(movement, 'comments', None),
            location=movement.location,
            created_by=movement.user_id,
            updated_by=movement.user_id,
            
            # FIFO & Compliance (Anexo 24)
            available_quantity=getattr(movement, 'available_quantity', Decimal("0.0")),
            customs_pedimento_id=getattr(movement, 'customs_pedimento_id', None),
            source_movement_id=getattr(movement, 'source_movement_id', None),
            expiry_date=getattr(movement, 'expiry_date', None),
            validation_status=getattr(movement, 'validation_status', "CLEAN")
        )

        self.session.add(movement_model)
        
        # We handle commitments in repository
        await self.session.flush()

        available = stock.available_quantity
        if available < Decimal(0):
            asyncio.create_task(
                TicketsClient.post_system_alert(
                    title=f"CRITICAL: Negative Available Stock",
                    description=f"Stock for Product {stock.product_id} broke safety parameters after movement.",
                    priority="P1_CRITICAL",
                    company_id=movement.company_id,
                    product_id=stock.product_id,
                    warehouse_id=stock.warehouse_id,
                    transaction_id=movement.id
                )
            )
        elif available <= Decimal(10) and available >= Decimal(0):
             asyncio.create_task(
                TicketsClient.post_system_alert(
                    title=f"WARNING: Reorder Point Reached",
                    description=f"Available stock for Product {stock.product_id} dropped to {available}.",
                    priority="P2_HIGH",
                    company_id=movement.company_id,
                    product_id=stock.product_id,
                    warehouse_id=stock.warehouse_id,
                    transaction_id=movement.id
                )
            )

        return self._to_level_entity(stock)

    async def reserve_stock(self, warehouse_id: uuid.UUID, product_id: uuid.UUID, quantity: Decimal, company_id: uuid.UUID) -> InventoryLevelEntity:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        stmt = select(InventoryLevel).filter_by(warehouse_id=warehouse_id, product_id=product_id, company_id=company_id)
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise ValueError("ERR_STOCK_NOT_FOUND: Product not found in warehouse.")
            
        if stock.available_quantity < quantity:
            raise ValueError(f"ERR_INSUFFICIENT_STOCK: Only {stock.available_quantity} available, {quantity} requested.")
            
        stock.reserved_quantity += quantity
        await self.session.flush()
        return self._to_level_entity(stock)

    async def force_release_orphan(self, warehouse_id: uuid.UUID, product_id: uuid.UUID, release_qty: Decimal, company_id: uuid.UUID) -> InventoryLevelEntity:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        stmt = select(InventoryLevel).filter_by(
            warehouse_id=warehouse_id,
            product_id=product_id,
            company_id=company_id
        ).with_for_update()
        
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise ValueError("ERR_STOCK_NOT_FOUND: Product not found in warehouse.")
            
        if stock.reserved_quantity < release_qty:
            raise ValueError(f"ERR_INVALID_RELEASE: Cannot release {release_qty}. Only {stock.reserved_quantity} reserved.")
            
        stock.reserved_quantity -= release_qty
        await self.session.flush()
        
        asyncio.create_task(
            TicketsClient.post_system_alert(
                title=f"AUDIT: Manual Reservation Release",
                description=f"A system admin forcibly released {release_qty} reserved units for Product {product_id}.",
                priority="P4_LOW",
                company_id=company_id,
                product_id=product_id,
                warehouse_id=warehouse_id
            )
        )
        return self._to_level_entity(stock)

    async def get_dashboard_stock(self, company_id: uuid.UUID) -> List[dict]:
        stmt = select(InventoryLevel).filter_by(company_id=company_id)
        result = await self.session.execute(stmt)
        stocks = {s.id: s for s in result.scalars().all()}.values()
        
        transit_uuids = {uuid.uuid5(uuid.NAMESPACE_OID, f"{s.warehouse_id}_transit") for s in stocks}
        
        final_rows = []
        for s in stocks:
            if s.warehouse_id in transit_uuids:
                continue 

            transit_uuid = uuid.uuid5(uuid.NAMESPACE_OID, f"{s.warehouse_id}_transit")
            transit_stock = next((t for t in stocks if t.warehouse_id == transit_uuid and t.product_id == s.product_id), None)
            
            final_rows.append({
                "product_id": s.product_id,
                "warehouse_id": s.warehouse_id,
                "total_quantity": s.quantity,
                "reserved_quantity": s.reserved_quantity,
                "available_quantity": s.available_quantity,
                "in_transit_quantity": transit_stock.quantity if transit_stock else Decimal("0.0")
            })
            
        return final_rows

    async def find_pending_for_reconciliation(self, company_id: Optional[uuid.UUID] = None, max_retries: int = 10) -> List[dict]:
        from inventory_app.models.backflush_error import BackflushError, BackflushStatus
        from datetime import datetime, timezone, timedelta
        
        stmt = select(BackflushError).where(
            BackflushError.status == BackflushStatus.PENDING,
            BackflushError.retry_count < max_retries
        )
        if company_id:
            stmt = stmt.where(BackflushError.company_id == company_id)
        
        result = await self.session.execute(stmt)
        all_pending = result.scalars().all()
        
        due_records = []
        now = datetime.now(timezone.utc)
        
        for record in all_pending:
            if not record.last_retry_at:
                due_records.append({"id": record.id, "error": record.error_details})
                continue
            
            wait_minutes = (2 ** record.retry_count) * 5
            if now > record.last_retry_at + timedelta(minutes=wait_minutes):
                due_records.append({"id": record.id, "error": record.error_details})
                
        return due_records

    async def update_reconciliation_status(self, error_id: uuid.UUID, success: bool, details: Optional[str] = None, company_id: Optional[uuid.UUID] = None):
        from inventory_app.models.backflush_error import BackflushError, BackflushStatus
        from datetime import datetime, timezone
        
        stmt = select(BackflushError).where(BackflushError.id == error_id)
        if company_id:
             stmt = stmt.where(BackflushError.company_id == company_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            return
            
        record.last_retry_at = datetime.now(timezone.utc)
        if success:
            record.status = BackflushStatus.RESOLVED
            record.error_details = details or "Resolved by worker"
        else:
            record.retry_count += 1
            record.error_details = details or record.error_details
            if record.retry_count >= 10:
                record.status = BackflushStatus.FAILED_MANUAL_REVIEW
        
        self.session.add(record)
        await self.session.flush()

    async def has_processed_document(self, document_type: str, document_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        stmt = select(Movement).filter_by(
            document_type=document_type,
            document_id=document_id,
            company_id=company_id
        )
        existing = await self.session.execute(stmt)
        return existing.scalar_one_or_none() is not None

    async def get_backflush_error(self, error_id: uuid.UUID, company_id: uuid.UUID) -> Optional[dict]:
        from inventory_app.models.backflush_error import BackflushError
        stmt = select(BackflushError).where(
            BackflushError.id == error_id,
            BackflushError.company_id == company_id
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return {"id": record.id, "status": getattr(record.status, "value", str(record.status)), "error_details": record.error_details}

    async def search_items_and_variants(self, query: str, company_id: uuid.UUID, limit: int = 10) -> List[dict]:
        from inventory_app.models.item_variant import ItemVariant
        from inventory_app.models.warehouse import Warehouse
        from sqlalchemy import or_, and_
        
        search_query = f"%{query}%"
        
        stmt = (
            select(
                ItemVariant.id.label("variant_id"),
                ItemVariant.internal_sku,
                ItemVariant.brand,
                ItemVariant.mfg_part_number,
                ItemVariant.weight,
                ItemVariant.volume,
                InventoryLevel.quantity,
                Warehouse.name.label("warehouse_name")
            )
            .join(InventoryLevel, InventoryLevel.product_id == ItemVariant.product_id)
            .join(Warehouse, Warehouse.id == InventoryLevel.warehouse_id)
            .where(
                and_(
                    ItemVariant.company_id == company_id,
                    InventoryLevel.company_id == company_id, # Redundant but safe
                    or_(
                        ItemVariant.internal_sku.ilike(search_query),
                        ItemVariant.mfg_part_number.ilike(search_query),
                        ItemVariant.brand.ilike(search_query)
                    )
                )
            )
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        final_results = []
        for r in rows:
            display_name = f"{r.internal_sku} | {r.brand} {r.mfg_part_number} ({r.warehouse_name})"
            final_results.append({
                "display_name": display_name,
                "sku_maestro": r.internal_sku,
                "variant_id": r.variant_id,
                "brand": r.brand,
                "mfg_part_number": r.mfg_part_number,
                "quantity": r.quantity,
                "weight": r.weight,
                "volume": r.volume,
                "warehouse_name": r.warehouse_name
            })
            
        return final_results

    async def get_inventory_summary(self, company_id: uuid.UUID, warehouse_id: Optional[uuid.UUID] = None) -> MovementSummaryEntity:
        from datetime import datetime, timedelta, timezone
        since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Aggregate counts for the last 24h
        stmt_summary = (
            select(
                func.count(func.distinct(Movement.document_id)).filter(Movement.movement_type == "IN").label("entries"),
                func.count(func.distinct(Movement.document_id)).filter(Movement.movement_type == "OUT").label("outputs"),
                func.count(func.distinct(Movement.document_id)).filter(Movement.movement_type == "TRANSFER").label("transfers")
            )
            .where(
                and_(
                    Movement.company_id == company_id,
                    Movement.created_at >= since_24h
                )
            )
        )

        if warehouse_id:
            stmt_summary = stmt_summary.where(Movement.warehouse_id == warehouse_id)
        
        # Pending documents (Status DRAFT)
        stmt_pending = (
            select(func.count(InventoryDocument.id))
            .where(
                and_(
                    InventoryDocument.company_id == company_id,
                    InventoryDocument.status == DocumentStatus.DRAFT
                )
            )
        )

        if warehouse_id:
            stmt_pending = stmt_pending.join(
                Movement, 
                Movement.document_id == InventoryDocument.id
            ).where(Movement.warehouse_id == warehouse_id).distinct()
        
        summary_result = await self.session.execute(stmt_summary)
        summary_row = summary_result.one()
        
        pending_result = await self.session.execute(stmt_pending)
        pending_count = pending_result.scalar()
        
        return MovementSummaryEntity(
            entries_24h=summary_row.entries or 0,
            outputs_24h=summary_row.outputs or 0,
            transfers_24h=summary_row.transfers or 0,
            pending_docs=pending_count or 0
        )

    async def list_movements(
        self,
        company_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        movement_type: Optional[str] = None,
        warehouse_id: Optional[uuid.UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> tuple[List[DocumentListRowEntity], int]:
        from datetime import datetime, timezone
        from sqlalchemy import func

        base_stmt = select(InventoryDocument).where(InventoryDocument.company_id == company_id)

        if warehouse_id:
            # Join with Movement to filter by warehouse (involved in any movement of this document)
            base_stmt = base_stmt.join(
                Movement, 
                Movement.document_id == InventoryDocument.id
            ).where(Movement.warehouse_id == warehouse_id).distinct()

        if movement_type:
            base_stmt = base_stmt.where(InventoryDocument.document_type == movement_type)

        if date_from:
            dt_from = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
            base_stmt = base_stmt.where(InventoryDocument.created_at >= dt_from)

        if date_to:
            dt_to = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
            base_stmt = base_stmt.where(InventoryDocument.created_at <= dt_to)

        # Count Query
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar() or 0

        stmt = base_stmt.order_by(InventoryDocument.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        docs = result.scalars().all()

        data = [
            DocumentListRowEntity(
                id=doc.id,
                folio=doc.folio,
                date=doc.created_at.isoformat(),
                type=doc.document_type,
                origin=doc.origin_name or "N/A",
                destination=doc.destination_name or "N/A",
                items_count=doc.total_items,
                total_weight=doc.total_weight,
                status=doc.status.value,
                trace_id=str(doc.id),
                external_reference=doc.external_reference,
                validation_status="CLEAN" # TODO: Aggregated status if needed
            )
            for doc in docs
        ]
        return data, total_count
    async def get_document_by_id(self, document_id: uuid.UUID, company_id: uuid.UUID) -> Optional[DocumentDetailEntity]:
        # 1. Fetch Document
        stmt_doc = select(InventoryDocument).where(
            and_(
                InventoryDocument.id == document_id,
                InventoryDocument.company_id == company_id
            )
        )
        doc_res = await self.session.execute(stmt_doc)
        doc = doc_res.scalar_one_or_none()
        if not doc:
            logger.warning(f"Document {document_id} not found for company {company_id}")
            return None

        # 2. Fetch Movements
        stmt_movs = (
            select(Movement)
            .where(
                and_(
                    Movement.document_id == document_id,
                    Movement.company_id == company_id
                )
            )
        )
        try:
            movs_res = await self.session.execute(stmt_movs)
            rows = movs_res.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching movements for document {document_id}: {str(e)}")
            rows = []

        items = []
        notes = None
        warehouse_id = None

        # Phase 33.5: Handle ICT_IN Drafts (Mirror Documents)
        if doc.document_type == "ICT_IN" and doc.status == DocumentStatus.DRAFT:
            stmt_ict = select(InterCompanyTransfer).where(InterCompanyTransfer.mirror_document_id == document_id)
            ict_res = await self.session.execute(stmt_ict)
            ict = ict_res.scalar_one_or_none()
            if ict:
                warehouse_id = ict.destination_warehouse_id
                notes = ict.notes
                # Fetch SKU and Name from the target company's catalog via ItemVariant
                stmt_sku = select(ItemVariant).where(
                    and_(
                        ItemVariant.product_id == ict.destination_product_id,
                        ItemVariant.company_id == company_id
                    )
                ).limit(1)
                sku_res = await self.session.execute(stmt_sku)
                variant = sku_res.scalar_one_or_none()
                
                items.append(DocumentItemEntity(
                    product_id=ict.destination_product_id,
                    sku=variant.internal_sku if variant else ict.destination_sku or "N/A",
                    name=variant.mfg_part_number if variant else "Inbound ICT Product",
                    quantity=ict.quantity,
                    uom_id=ict.uom_id,
                    uom_name="PZA", 
                    weight=ict.weight,
                    location="REC-DOCK"
                ))

        for m in rows:
            if not warehouse_id:
                warehouse_id = m.warehouse_id
            if not notes:
                notes = m.comments
            
            # Resolve SKU and Name for each unique product in this document
            # To keep it efficient, we could cache this, but for a single document detail it's fine
            stmt_variant = select(ItemVariant).where(
                and_(
                    ItemVariant.product_id == m.product_id,
                    ItemVariant.company_id == company_id
                )
            ).limit(1)
            v_res = await self.session.execute(stmt_variant)
            variant = v_res.scalar_one_or_none()

            items.append(DocumentItemEntity(
                product_id=m.product_id,
                sku=variant.internal_sku if variant else "N/A",
                name=variant.mfg_part_number if variant else "Producto Industrial",
                quantity=m.quantity,
                uom_id=m.uom_id,
                uom_name="PZA", # TODO: Resolve UOM name
                weight=m.weight,
                unit_price=m._amount if m._amount is not None else Decimal("0.0"),
                location=m.location,
                validation_status=m.validation_status
            ))



        try:
            return DocumentDetailEntity(
                id=doc.id,
                folio=doc.folio,
                date=doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat(),
                type=doc.document_type,
                status=getattr(doc.status, "value", str(doc.status)),
                origin=doc.origin_name or "N/A",
                destination=doc.destination_name or "N/A",
                items_count=doc.total_items,
                total_weight=doc.total_weight,
                concept_id=doc.concept_id,
                warehouse_id=warehouse_id,
                notes=notes,
                items=items
            )
        except Exception as e:
            logger.error(f"Error mapping document entity for {document_id}: {str(e)}")
            # Fallback to avoid 500
            return DocumentDetailEntity(
                id=doc.id,
                folio=doc.folio,
                date=datetime.now().isoformat(),
                type=doc.document_type,
                status="ERROR",
                origin="N/A",
                destination="N/A",
                items_count=0,
                total_weight=Decimal("0"),
                items=[]
            )


    # ─── A. KARDEX: Running Balance (Window Function) ──────────────────────────────

    async def get_kardex(
        self,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        company_id: uuid.UUID,
        limit: int = 200
    ) -> List[KardexRowEntity]:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        """
        Calculates running balance (Kardex) for a specific SKU/Warehouse
        using a SQL Window Function: SUM(quantity) OVER (ORDER BY created_at).
        """
        from sqlalchemy import over, case

        signed_qty = case(
            {Movement.movement_type == "OUT": -Movement.quantity},
            else_=Movement.quantity
        ).label("quantity_delta")

        running_balance = func.sum(
            case(
                {Movement.movement_type == "OUT": -Movement.quantity},
                else_=Movement.quantity
            )
        ).over(
            order_by=Movement.created_at,
            rows=(None, 0)  # ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ).label("running_balance")

        stmt = (
            select(
                Movement.id.label("movement_id"),
                Movement.created_at,
                Movement.document_id,
                Movement.movement_type,
                signed_qty,
                Movement.uom_id,
                Movement.weight,
                Movement.price,
                running_balance,
                Movement.company_id,
                Movement.validation_status
            )
            .where(
                and_(
                    Movement.product_id == product_id,
                    Movement.warehouse_id == warehouse_id,
                    Movement.company_id == company_id
                )
            )
            .order_by(Movement.created_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            KardexRowEntity(
                movement_id=r.movement_id,
                date=r.created_at.isoformat(),
                document_folio=str(r.document_id),  # folio lookup optional via join
                movement_type=r.movement_type,
                quantity_delta=r.quantity_delta,
                uom_id=r.uom_id,
                weight=r.weight,
                price=r.price,
                running_balance=r.running_balance,
                company_id=r.company_id,
                validation_status=r.validation_status
            )
            for r in rows
        ]

    # ─── B. WAC VALUATION (Weighted Average Cost) ───────────────────────────────

    async def get_wac_valuation(
        self,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        company_id: uuid.UUID,
        as_of_date: Optional[str] = None
    ) -> Optional[WACValuationEntity]:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        """
        Computes Weighted Average Cost by iterating the immutable Movement ledger.
        WAC = SUM(qty_in * price) / SUM(qty_in)
        Only IN movements with a price > 0 are considered for cost basis.
        """
        from datetime import datetime, timezone

        from sqlalchemy import case

        stmt = (
            select(
                func.sum(Movement.quantity).label("total_units"),
                func.sum(
                    case(
                        {
                            and_(
                                Movement.movement_type == "IN",
                                Movement._amount > 0
                            ): Movement.quantity * Movement._amount
                        },
                        else_=Decimal("0")
                    )
                ).label("total_cost_basis"),
                func.sum(
                    case(
                        {
                            and_(
                                Movement.movement_type == "IN",
                                Movement._amount > 0
                            ): Movement.quantity
                        },
                        else_=Decimal("0")
                    )
                ).label("total_priced_units")
            )
            .where(
                and_(
                    Movement.product_id == product_id,
                    Movement.warehouse_id == warehouse_id,
                    Movement.company_id == company_id
                )
            )
        )

        if as_of_date:
            dt = datetime.fromisoformat(as_of_date).replace(tzinfo=timezone.utc)
            stmt = stmt.where(Movement.created_at <= dt)

        result = await self.session.execute(stmt)
        row = result.one()

        total_units = row.total_units or Decimal("0")
        total_priced_units = row.total_priced_units or Decimal("1")
        cost_basis = row.total_cost_basis or Decimal("0")

        wac_amount = (cost_basis / total_priced_units) if total_priced_units > 0 else Decimal("0")
        
        # We need a currency for the WAC valuation. We can pick from the last movement or default to MXN.
        # For now, let's assume the company's base currency or the level's currency.
        currency = "MXN" # Default
        
        return WACValuationEntity(
            product_id=product_id,
            warehouse_id=warehouse_id,
            as_of_date=as_of_date or datetime.now(timezone.utc).isoformat(),
            total_units=total_units,
            wac=Money(amount=wac_amount, currency=currency),
            total_inventory_value=Money(amount=total_units * wac_amount, currency=currency),
            company_id=company_id
        )

    # ─── C. ABC ROTATION ANALYTICS ────────────────────────────────────────────

    async def get_abc_rotation(
        self,
        company_id: uuid.UUID,
        warehouse_id: Optional[uuid.UUID] = None
    ) -> List[RotationABCEntity]:
        """
        Computes ABC rotation class for each product:
        - Class A: rotation_index_30d >= 0.7  (fast-movers)
        - Class B: 0.3 <= rotation_index_30d < 0.7
        - Class C: rotation_index_30d < 0.3   (slow-movers)
        """
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        since_30d = now - timedelta(days=30)
        since_90d = now - timedelta(days=90)

        # 1. Current stock per product/warehouse
        stock_stmt = select(
            InventoryLevel.product_id,
            InventoryLevel.warehouse_id,
            InventoryLevel.quantity.label("current_stock"),
            InventoryLevel.company_id
        ).where(InventoryLevel.company_id == company_id)

        if warehouse_id:
            await self._validate_warehouse_ownership(warehouse_id, company_id)
            stock_stmt = stock_stmt.where(InventoryLevel.warehouse_id == warehouse_id)

        stock_result = await self.session.execute(stock_stmt)
        stocks = {(r.product_id, r.warehouse_id): r for r in stock_result.all()}

        if not stocks:
            return []

        # 2. Exit volumes: grouped by product/warehouse in 30d and 90d windows
        def exit_vol_stmt(since):
            filters = [
                Movement.company_id == company_id,
                Movement.movement_type == "OUT",
                Movement.created_at >= since
            ]
            if warehouse_id:
                filters.append(Movement.warehouse_id == warehouse_id)
            return (
                select(
                    Movement.product_id,
                    Movement.warehouse_id,
                    func.sum(Movement.quantity).label("exits")
                )
                .where(and_(*filters))
                .group_by(Movement.product_id, Movement.warehouse_id)
            )

        exits_30_result = await self.session.execute(exit_vol_stmt(since_30d))
        exits_30 = {(r.product_id, r.warehouse_id): r.exits for r in exits_30_result.all()}

        exits_90_result = await self.session.execute(exit_vol_stmt(since_90d))
        exits_90 = {(r.product_id, r.warehouse_id): r.exits for r in exits_90_result.all()}

        # 3. Compose result
        results = []
        for (prod_id, wh_id), stock_row in stocks.items():
            current = stock_row.current_stock or Decimal("0")
            e30 = exits_30.get((prod_id, wh_id), Decimal("0")) or Decimal("0")
            e90 = exits_90.get((prod_id, wh_id), Decimal("0")) or Decimal("0")

            rotation = e30 / (current + Decimal("0.0001"))

            if rotation >= Decimal("0.7"):
                abc = "A"
            elif rotation >= Decimal("0.3"):
                abc = "B"
            else:
                abc = "C"

            results.append(RotationABCEntity(
                product_id=prod_id,
                warehouse_id=wh_id,
                current_stock=current,
                exits_30d=e30,
                exits_90d=e90,
                rotation_index_30d=rotation.quantize(Decimal("0.0001")),
                abc_class=abc,
                company_id=company_id
            ))

        return sorted(results, key=lambda x: x.rotation_index_30d, reverse=True)

    async def search_inventory_products(
        self,
        query: str,
        company_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        limit: int = 10
    ) -> List[InventorySearchRowEntity]:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        from inventory_app.models.item_variant import ItemVariant
        from sqlalchemy import or_, and_
        from datetime import datetime, timedelta, timezone

        search_query = f"%{query}%"

        # 1. Base results: Variants + Stock level (Outer Join)
        stmt = (
            select(
                ItemVariant.product_id,
                ItemVariant.internal_sku,
                ItemVariant.brand,
                ItemVariant.mfg_part_number,
                InventoryLevel.quantity,
                InventoryLevel.uom_id
            )
            .outerjoin(
                InventoryLevel, 
                and_(
                    InventoryLevel.product_id == ItemVariant.product_id,
                    InventoryLevel.warehouse_id == warehouse_id
                )
            )
            .where(
                and_(
                    ItemVariant.company_id == company_id,
                    or_(
                        ItemVariant.internal_sku.ilike(search_query),
                        ItemVariant.mfg_part_number.ilike(search_query),
                        ItemVariant.brand.ilike(search_query)
                    )
                )
            )
            .limit(limit)
        )

        db_result = await self.session.execute(stmt)
        rows = db_result.all()

        if not rows:
            return []

        # 2. Rotation Calculation (A/B/C) for the found products
        product_ids = [r.product_id for r in rows]
        now = datetime.now(timezone.utc)
        since_30d = now - timedelta(days=30)

        # Exit volumes in 30d for these products
        exit_stmt = (
            select(
                Movement.product_id,
                func.sum(Movement.quantity).label("exits")
            )
            .where(
                and_(
                    Movement.company_id == company_id,
                    Movement.warehouse_id == warehouse_id,
                    Movement.movement_type == "OUT",
                    Movement.created_at >= since_30d,
                    Movement.product_id.in_(product_ids)
                )
            )
            .group_by(Movement.product_id)
        )

        exit_result = await self.session.execute(exit_stmt)
        exits = {r.product_id: (r.exits or Decimal("0")) for r in exit_result.all()}

        # 3. Build Final Entities
        final_results = []
        for r in rows:
            current = r.quantity or Decimal("0")
            e30 = exits.get(r.product_id, Decimal("0"))
            
            # Simple rotation index: exits / (current + epsilon)
            rotation = e30 / (current + Decimal("0.0001"))
            
            abc_class = "C"
            if rotation >= Decimal("0.7"):
                abc_class = "A"
            elif rotation >= Decimal("0.3"):
                abc_class = "B"
            
            # Fallback for uom_id if item has no stock records yet
            # UOM_PZ_ID from seed = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")
            uom_id = r.uom_id or uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")
            
            final_results.append(InventorySearchRowEntity(
                id=r.product_id,
                sku=r.internal_sku,
                name=f"{r.brand} {r.mfg_part_number}",
                current_stock=current,
                uom_id=uom_id,
                uom_symbol="PZA", # Standard fallback
                abc_class=abc_class,
                company_id=company_id
            ))
            
        return final_results

    async def get_dashboard_telemetry(self, warehouse_id: uuid.UUID, company_id: uuid.UUID) -> DashboardTelemetryEntity:
        await self._validate_warehouse_ownership(warehouse_id, company_id)
        """
        Calcula métricas clave para el dashboard: valoración total, alertas y serie temporal.
        Optimizado con DISTINCT ON para valoración y date_trunc para series temporales.
        """
        # 1. Valoración Total (Latest Unit Price JOIN)
        # Obtenemos el precio unitario más reciente por producto (excluyendo TRANSFER)
        latest_prices_stmt = select(
            Movement.product_id,
            Movement._amount.label("unit_price")
        ).distinct(Movement.product_id).where(
            and_(
                Movement.company_id == company_id,
                Movement.warehouse_id == warehouse_id,
                Movement.movement_type != "TRANSFER",
                Movement._amount > 0
            )
        ).order_by(Movement.product_id, desc(Movement.created_at))
        
        latest_prices_sub = latest_prices_stmt.subquery()
        
        valuation_stmt = select(
            func.coalesce(func.sum(InventoryLevel.quantity * latest_prices_sub.c.unit_price), 0)
        ).select_from(
            InventoryLevel
        ).join(
            latest_prices_sub, InventoryLevel.product_id == latest_prices_sub.c.product_id
        ).where(
            and_(
                InventoryLevel.warehouse_id == warehouse_id,
                InventoryLevel.company_id == company_id
            )
        )
        
        val_result = await self.session.execute(valuation_stmt)
        valuation_total = Decimal(str(val_result.scalar() or "0.0"))

        # 2. Alertas Críticas (Threshold Placeholder)
        # Recuperamos items con stock bajo para que el Handler los enriquezca con Master Data
        alerts_stmt = select(
            InventoryLevel.product_id,
            InventoryLevel.quantity
        ).where(
            and_(
                InventoryLevel.warehouse_id == warehouse_id,
                InventoryLevel.company_id == company_id,
                InventoryLevel.quantity <= 10  # Umbral de seguridad para reporte
            )
        ).limit(10)
        
        alerts_result = await self.session.execute(alerts_stmt)
        alerts = [
            StockAlertEntity(
                product_id=row.product_id,
                sku=f"SKU-{str(row.product_id)[:4].upper()}", # Placeholder a ser sobreescrito por MD Client
                current_quantity=row.quantity,
                min_quantity=Decimal("10.0"), # Static threshold for now
                warehouse_id=warehouse_id,
                status="CRITICAL" if row.quantity <= 0 else "LOW"
            ) for row in alerts_result.all()
        ]

        # 3. Serie Temporal (Hourly Aggregation)
        # Agrupación por hora de los movimientos del último día
        since_24h = datetime.utcnow() - timedelta(hours=24)
        hourly_stmt = select(
            func.date_trunc('hour', Movement.created_at).label('hour'),
            func.coalesce(func.sum(case((Movement.movement_type == 'IN', Movement.quantity), else_=0)), 0).label('entries'),
            func.coalesce(func.sum(case((Movement.movement_type == 'OUT', Movement.quantity), else_=0)), 0).label('exits')
        ).where(
            and_(
                Movement.warehouse_id == warehouse_id,
                Movement.company_id == company_id,
                Movement.created_at >= since_24h
            )
        ).group_by(text('hour')).order_by(text('hour'))
        
        hourly_result = await self.session.execute(hourly_stmt)
        hourly_series = [
            HourlyMovementEntity(
                hour=row.hour,
                entries=row.entries or Decimal("0.0"),
                exits=row.exits or Decimal("0.0")
            ) for row in hourly_result.all()
        ]

        # 4. Actividad Reciente (Across all SKUs)
        recent_stmt = select(
            Movement, 
            InventoryDocument.folio
        ).outerjoin(
            InventoryDocument, Movement.document_id == InventoryDocument.id
        ).where(
            and_(
                Movement.warehouse_id == warehouse_id,
                Movement.company_id == company_id
            )
        ).order_by(desc(Movement.created_at)).limit(10)
        
        recent_res = await self.session.execute(recent_stmt)
        recent_entities = [
            KardexRowEntity(
                movement_id=m.id,
                date=m.created_at.isoformat(),
                document_folio=folio or f"{m.document_type}-{str(m.document_id)[:4].upper()}",
                movement_type=m.movement_type,
                quantity_delta=m.quantity if m.movement_type == 'IN' else -m.quantity,
                uom_id=m.uom_id,
                weight=m.weight,
                price=m.price,
                running_balance=Decimal("0.0"), # Informativo, no acumulado
                company_id=company_id,
                validation_status=m.validation_status
            ) for m, folio in recent_res.all()
        ]

        return DashboardTelemetryEntity(
            valuation_total=valuation_total,
            critical_alerts_count=len(alerts),
            alerts=alerts,
            hourly_series=hourly_series,
            recent_movements=recent_entities
        )

    async def get_warehouse_owner_id(self, warehouse_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Optional[uuid.UUID]:
        """Recupera el company_id propietario de un almacén local."""
        from inventory_app.models.warehouse import Warehouse
        stmt = select(Warehouse.company_id).where(Warehouse.id == warehouse_id)
        if company_id:
             stmt = stmt.where(Warehouse.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_inventory_document(self, document_entity: dict, company_id: uuid.UUID) -> Any:
        # 1. Forensic Guard: Ensure company_id is a UUID object
        strict_company_id = company_id
        if isinstance(strict_company_id, str):
            try:
                strict_company_id = uuid.UUID(strict_company_id)
            except:
                pass

        # 2. Map Entity to Model
        import uuid as py_uuid
        from inventory_app.models.document import InventoryDocument, DocumentStatus
        from decimal import Decimal
        from common.domain.value_objects import Money

        new_doc = InventoryDocument(
            id=document_entity.get("id") or py_uuid.uuid4(),
            folio=document_entity.get("folio") or f"DOC-{str(py_uuid.uuid4())[:8].upper()}",
            document_type=document_entity.get("document_type", "ENTRY"),
            status=document_entity.get("status", DocumentStatus.PROCESSED),
            origin_name=document_entity.get("origin_name"),
            destination_name=document_entity.get("destination_name"),
            total_items=document_entity.get("total_items", 0),
            total_weight=Decimal(str(document_entity.get("total_weight", 0.0))),
            concept_id=document_entity.get("concept_id"),
            external_reference=str(document_entity.get("external_reference", py_uuid.uuid4())),
            company_id=strict_company_id,
            tenant_id=strict_company_id
        )
        
        # Financial aggregate
        new_doc.total_currency = document_entity.get("total_currency", "MXN")
        new_doc.total_amount_val = Decimal(str(document_entity.get("total_amount", 0.0)))

        self.session.add(new_doc)
        await self.session.flush()
        return new_doc

    async def ensure_transit_warehouse(self, to_warehouse_id: uuid.UUID, company_id: uuid.UUID) -> uuid.UUID:
        """Asegura que el almacén de tránsito (virtual) para el destino exista localmente."""
        from inventory_app.models.warehouse import Warehouse
        # Deterministic Transit ID for the destination warehouse
        transit_id = uuid.uuid5(uuid.NAMESPACE_OID, f"{to_warehouse_id}_transit")
        
        # 1. First, check if it already exists (including soft-deleted)
        stmt = select(Warehouse).where(Warehouse.id == transit_id)
        result = await self.session.execute(stmt)
        existing_wh = result.scalar_one_or_none()
        
        if existing_wh:
            # Healing: Ensure it has the correct owner (in case it was created with another company previously)
            if existing_wh.company_id != company_id:
                logger.warning(f"[PROVISION] Transit warehouse {transit_id} already exists with WRONG company {existing_wh.company_id}. Updating to {company_id}")
                existing_wh.company_id = company_id
                existing_wh.tenant_id = company_id
                await self.session.flush()
            return transit_id

        # 2. Provision virtual transit warehouse
        try:
            transit_wh = Warehouse(
                id=transit_id,
                company_id=company_id,
                tenant_id=company_id,
                code="IN-TRANSIT",
                name="In-Transit Warehouse",
                is_transit=True,
                country_code="MX"
            )
            # Mandatory multi-tenant fields
            transit_wh.company_id = company_id
            transit_wh.tenant_id = company_id
            
            self.session.add(transit_wh)
            await self.session.flush()
            logger.info(f"[PROVISION] Created virtual transit warehouse {transit_id} for company {company_id}")
        except Exception as e:
            # Handle potential race conditions: if it was created by another simultaneous request
            self.session.rollback() # Rollback the collision
            logger.error(f"[PROVISION] Race condition or error creating transit warehouse {transit_id}: {str(e)}")
            # Retry one last find
            stmt = select(Warehouse).where(Warehouse.id == transit_id)
            res = await self.session.execute(stmt)
            if not res.scalar_one_or_none():
                raise e # Real failure

        return transit_id

    async def get_customs_balances(
        self, 
        company_id: uuid.UUID, 
        warehouse_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
        query: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """
        Customs Balance Report (Phase 42.3 / Anexo 24).
        Retorna agregación por SKU y Pedimento con saldo residual y vencimientos.
        Optimizado para escalabilidad industrial (10k+ items) mediante paginación y búsqueda.
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # 1. Base Query: Agrupación por Producto y Pedimento
        # Solo consideramos movimientos con saldo residual (available_quantity > 0)
        base_stmt = (
            select(
                Movement.product_id,
                ItemVariant.internal_sku,
                ItemVariant.mfg_part_number.label("product_name"),
                Movement.customs_pedimento_id,
                CustomsPedimento.pedimento_number,
                func.sum(Movement.available_quantity).label("total_available_qty"),
                Movement.expiry_date
            )
            .outerjoin(CustomsPedimento, Movement.customs_pedimento_id == CustomsPedimento.id)
            .outerjoin(ItemVariant, and_(
                Movement.product_id == ItemVariant.product_id,
                Movement.company_id == ItemVariant.company_id
            ))
            .where(
                and_(
                    Movement.company_id == company_id,
                    Movement.available_quantity > 0
                )
            )
        )

        if warehouse_id:
            base_stmt = base_stmt.where(Movement.warehouse_id == warehouse_id)

        if query:
            search_pattern = f"%{query}%"
            base_stmt = base_stmt.where(
                or_(
                    ItemVariant.internal_sku.ilike(search_pattern),
                    ItemVariant.mfg_part_number.ilike(search_pattern),
                    CustomsPedimento.pedimento_number.ilike(search_pattern)
                )
            )

        # Agrupación estricta por SKU/Pedimento/Vencimiento
        grouped_stmt = base_stmt.group_by(
            Movement.product_id,
            ItemVariant.internal_sku, 
            ItemVariant.mfg_part_number,
            Movement.customs_pedimento_id,
            CustomsPedimento.pedimento_number,
            Movement.expiry_date
        )

        # 2. Total Count (using subquery to count unique groups)
        subquery = grouped_stmt.subquery()
        count_stmt = select(func.count()).select_from(subquery)
        total_count_res = await self.session.execute(count_stmt)
        total_count = total_count_res.scalar() or 0

        # 3. Paginated Results
        # Ordenar por el más antiguo primero (FIFO Risk)
        final_stmt = grouped_stmt.order_by(
            Movement.expiry_date.asc().nulls_last()
        ).limit(limit).offset(offset)

        result = await self.session.execute(final_stmt)
        rows = result.all()

        report_data = []
        for r in rows:
            days_to_expiry = None
            is_at_risk = False
            
            if r.expiry_date:
                expiry = r.expiry_date
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                
                delta = expiry - now
                days_to_expiry = delta.days
                is_at_risk = days_to_expiry < 30 # Alerta Anexo 24 (IEPS Risk)

            report_data.append({
                "item_id": r.product_id,
                "sku": r.internal_sku or "N/A",
                "product_name": r.product_name or "N/A",
                "customs_pedimento_id": r.customs_pedimento_id,
                "pedimento_number": r.pedimento_number or "SIN_PEDIMENTO",
                "total_available_qty": r.total_available_qty,
                "expiry_date": r.expiry_date,
                "days_to_expiry": days_to_expiry,
                "is_at_risk": is_at_risk
            })

        return report_data, total_count

    async def get_available_movements_fifo(
        self,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        company_id: uuid.UUID
    ) -> List[MovementEntity]:
        """
        Calculates the available stock-bearing movements (IN, TRANSFER_IN, etc.)
        sorted by FIFO (Customs Date or Created At).
        """
        from sqlalchemy import asc, func
        
        query = (
            select(
                Movement,
                CustomsPedimento.customs_date
            )
            .outerjoin(CustomsPedimento, Movement.customs_pedimento_id == CustomsPedimento.id)
            .where(
                Movement.product_id == product_id,
                Movement.warehouse_id == warehouse_id,
                Movement.company_id == company_id,
                Movement.available_quantity > 0
            )
            .order_by(
                asc(func.coalesce(CustomsPedimento.customs_date, Movement.created_at)),
                asc(Movement.created_at)
            )
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        entities = []
        for m, c_date in rows:
            entity = MovementEntity(
                id=m.id,
                warehouse_id=m.warehouse_id,
                product_id=m.product_id,
                company_id=m.company_id,
                quantity=m.quantity,
                uom_id=m.uom_id,
                weight=m.weight,
                price=m.price,
                movement_type=m.movement_type,
                document_type=m.document_type,
                document_id=m.document_id,
                available_quantity=m.available_quantity,
                customs_pedimento_id=m.customs_pedimento_id,
                expiry_date=m.expiry_date,
                created_at=m.created_at
            )
            entities.append(entity)
            
        return entities

    async def get_warehouse_entity(self, warehouse_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Any:
        """
        Recupera los detalles de un almacén como Entidad de Dominio.
        """
        from inventory_app.models.warehouse import Warehouse
        stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
        if company_id:
             stmt = stmt.where(Warehouse.company_id == company_id)
        result = await self.session.execute(stmt)
        wh = result.scalar_one_or_none()
        if not wh:
            return None
        return wh # Simplified


    async def consume_movement_balance(self, movement_id: uuid.UUID, quantity: Decimal, company_id: Optional[uuid.UUID] = None):
        """
        [Phase 42.6] Decrements the available_quantity of a specific movement record.
        This is core for FIFO/Anexo 24 consumption at the Kardex level.
        """
        import sqlalchemy as sa
        from inventory_app.models.movement import Movement
        stmt = (
            sa.update(Movement)
            .where(Movement.id == movement_id)
        )
        if company_id:
             stmt = stmt.where(Movement.company_id == company_id)
        
        stmt = stmt.values(available_quantity=Movement.available_quantity - quantity)
        await self.session.execute(stmt)
        # Flush is enough for the current Unit of Work
        await self.session.flush()
        # Simplified: We just need country_code for audit
        return {
            "id": wh.id,
            "company_id": wh.company_id,
            "country_code": wh.country_code or "MX",
            "name": wh.name
        }

    async def get_variants_by_product(self, product_id: uuid.UUID, company_id: uuid.UUID) -> List[ItemVariant]:
        stmt = select(ItemVariant).where(
            ItemVariant.product_id == product_id,
            ItemVariant.company_id == company_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_variant(self, variant_data: dict, company_id: uuid.UUID) -> ItemVariant:
        variant_id = variant_data.get("id")
        if variant_id:
            stmt = select(ItemVariant).where(ItemVariant.id == variant_id, ItemVariant.company_id == company_id)
            res = await self.session.execute(stmt)
            variant = res.scalar_one_or_none()
        else:
            variant = None

        if not variant:
            # Check for UQ collision (internal_sku + mfg_part_number)
            stmt = select(ItemVariant).where(
                ItemVariant.company_id == company_id,
                ItemVariant.internal_sku == variant_data["internal_sku"],
                ItemVariant.mfg_part_number == variant_data["mfg_part_number"]
            )
            res = await self.session.execute(stmt)
            variant = res.scalar_one_or_none()

        if variant:
            for k, v in variant_data.items():
                if hasattr(variant, k) and k != "id":
                    setattr(variant, k, v)
        else:
            # Generate ID if missing
            if "id" not in variant_data:
                variant_data["id"] = uuid.uuid4()
            
            variant = ItemVariant(**variant_data)
            variant.company_id = company_id
            variant.tenant_id = company_id
            self.session.add(variant)
        
        await self.session.flush()
        return variant

    async def get_quick_catalog(self, company_id: uuid.UUID) -> List[dict]:
        """
        Recupera una lista ligera de todos los productos (SKU + Nombre) para caché local.
        """
        stmt = select(
            ItemVariant.product_id,
            ItemVariant.internal_sku.label("sku"),
            ItemVariant.brand,
            ItemVariant.mfg_part_number.label("mpn")
        ).where(ItemVariant.company_id == company_id)
        
        result = await self.session.execute(stmt)
        return [
            {
                "id": str(r.product_id),
                "sku": r.sku,
                "name": f"{r.brand} {r.mpn}"
            }
            for r in result.all()
        ]

    async def get_location_occupancy(self, warehouse_id: uuid.UUID, location_code: str, company_id: uuid.UUID) -> Decimal:
        """
        Calcula la cantidad total de piezas actualmente en una ubicación (sumando saldos FIFO).
        """
        stmt = select(func.sum(Movement.available_quantity)).where(
            and_(
                Movement.warehouse_id == warehouse_id,
                Movement.location == location_code,
                Movement.company_id == company_id,
                Movement.available_quantity > 0
            )
        )
        result = await self.session.execute(stmt)
        val = result.scalar()
        return Decimal(str(val)) if val is not None else Decimal("0.0")

    async def get_location_capacity(self, warehouse_id: uuid.UUID, location_code: str, company_id: uuid.UUID) -> Decimal:
        """
        Recupera la capacidad máxima configurada. Retorna 0 si no hay límite definido.
        """
        from inventory_app.models.location import InventoryLocation
        stmt = select(InventoryLocation.max_capacity).where(
            and_(
                InventoryLocation.warehouse_id == warehouse_id,
                InventoryLocation.code == location_code,
                InventoryLocation.company_id == company_id
            )
        )
        result = await self.session.execute(stmt)
        capacity = result.scalar()
        return Decimal(str(capacity)) if capacity is not None else Decimal("0.0")

    async def get_detailed_stock_report(self, warehouse_id: uuid.UUID, company_id: uuid.UUID) -> List[dict]:
        """
        Genera el listado detallado de existencias para auditoría física.
        Incluye Ubicación, SKU, Pedimento, Lote y Cantidad Disponible.
        """
        from inventory_app.models.customs import CustomsPedimento
        from inventory_app.models.item_variant import ItemVariant

        stmt = (
            select(
                Movement.location,
                ItemVariant.internal_sku,
                ItemVariant.brand,
                CustomsPedimento.pedimento_number,
                Movement.available_quantity,
                Movement.expiry_date
            )
            .outerjoin(CustomsPedimento, Movement.customs_pedimento_id == CustomsPedimento.id)
            .outerjoin(ItemVariant, and_(
                Movement.product_id == ItemVariant.product_id,
                Movement.company_id == ItemVariant.company_id,
                ItemVariant.is_preferred == True
            ))

            .where(
                and_(
                    Movement.warehouse_id == warehouse_id,
                    Movement.company_id == company_id,
                    Movement.available_quantity > 0
                )
            )
            .order_by(Movement.location, ItemVariant.internal_sku)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {
                "location": r.location or "SIN_UBICACION",
                "sku": r.internal_sku or "N/A",
                "description": r.brand or "N/A",
                "pedimento": r.pedimento_number or "SIN_PEDIMENTO",
                "quantity": float(r.available_quantity),
                "expiry": r.expiry_date.isoformat() if r.expiry_date else None
            }
            for r in rows
        ]


