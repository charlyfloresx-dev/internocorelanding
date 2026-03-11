from typing import List, Optional
import uuid
import asyncio
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.entities.inventory_item import (
    InventoryLevelEntity, 
    InventoryTransactionEntity,
    MovementEntity
)
from app.models.stock import Stock
from app.models.movement import Movement
from app.infrastructure.tickets_client import TicketsClient

class SQLAlchemyInventoryRepository(IInventoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_level_entity(self, stock_model: Stock) -> InventoryLevelEntity:
        return InventoryLevelEntity(
            warehouse_id=stock_model.warehouse_id,
            product_id=stock_model.product_id,
            uom_id=stock_model.product_id, # Simplified for now, or fetch from model if available
            quantity=stock_model.quantity,
            reserved_quantity=stock_model.reserved_quantity,
            weighted_average_cost=Decimal("0.0"),
            last_purchase_price=Decimal("0.0"),
            replacement_price=Decimal("0.0"),
            currency_code="USD",
            company_id=stock_model.company_id
        )

    async def get_stock(self, warehouse_id: uuid.UUID, product_id: uuid.UUID, company_id: uuid.UUID) -> Optional[InventoryLevelEntity]:
        stmt = select(Stock).filter_by(
            warehouse_id=warehouse_id,
            product_id=product_id,
            company_id=company_id
        )
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()
        return self._to_level_entity(stock) if stock else None

    async def record_movement(self, movement: MovementEntity, allow_negative: bool = False, from_reservation: bool = False) -> InventoryLevelEntity:
        stmt = select(Stock).filter_by(
            warehouse_id=movement.warehouse_id,
            product_id=movement.product_id,
            company_id=movement.company_id
        )
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()
        
        if not stock:
            stock = Stock(
                warehouse_id=movement.warehouse_id,
                product_id=movement.product_id,
                company_id=movement.company_id,
                quantity=0
            )
            self.session.add(stock)

        new_quantity = stock.quantity + movement.quantity
        if new_quantity < 0 and not allow_negative:
            raise ValueError("ERR_INSUFFICIENT_STOCK: Transaction aborted.")

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
            quantity=movement.quantity,
            movement_type=movement.movement_type,
            document_type=movement.document_type,
            document_id=movement.document_id
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
        stmt = select(Stock).filter_by(warehouse_id=warehouse_id, product_id=product_id, company_id=company_id)
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
        stmt = select(Stock).filter_by(
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
        stmt = select(Stock).filter_by(company_id=company_id)
        result = await self.session.execute(stmt)
        stocks = result.scalars().all()
        
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

    async def find_pending_for_reconciliation(self, max_retries: int = 10) -> List[dict]:
        from app.models.backflush_error import BackflushError, BackflushStatus
        from datetime import datetime, timezone, timedelta
        
        stmt = select(BackflushError).where(
            BackflushError.status == BackflushStatus.PENDING,
            BackflushError.retry_count < max_retries
        )
        
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

    async def update_reconciliation_status(self, error_id: uuid.UUID, success: bool, details: Optional[str] = None):
        from app.models.backflush_error import BackflushError, BackflushStatus
        from datetime import datetime, timezone
        
        stmt = select(BackflushError).where(BackflushError.id == error_id)
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
        from app.models.backflush_error import BackflushError
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
        from app.models.item_variant import ItemVariant
        from app.models.warehouse import Warehouse
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
                Stock.quantity,
                Warehouse.name.label("warehouse_name")
            )
            .join(Stock, Stock.product_id == ItemVariant.product_id)
            .join(Warehouse, Warehouse.id == Stock.warehouse_id)
            .where(
                and_(
                    ItemVariant.company_id == company_id,
                    Stock.company_id == company_id, # Redundant but safe
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
