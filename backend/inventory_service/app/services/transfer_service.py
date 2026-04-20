import uuid
import logging
from typing import Optional, Any
from decimal import Decimal
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money

logger = logging.getLogger(__name__)

class TransferService:
    def __init__(self, repo: IInventoryRepository):
        self.repository = repo

    async def _check_location_capacity(self, warehouse_id: uuid.UUID, location_code: str, quantity: Decimal, company_id: uuid.UUID):
        """
        [DEPRECATED in Phase 63] Integrated Density Guard for Service level transfers.
        Now replaced by run_density_guard_audit in the background.
        """
        pass

    async def dispatch_transfer(
        self, 
        from_warehouse_id: uuid.UUID, 
        to_warehouse_id: uuid.UUID, 
        product_id: uuid.UUID, 
        quantity: Decimal, 
        uom_id: uuid.UUID, 
        weight: Decimal, 
        company_id: uuid.UUID, 
        transfer_id: uuid.UUID,
        selected_batch_id: Optional[uuid.UUID] = None
    ) -> MovementEntity:
        """
        Moves stock from source to IN_TRANSIT virtual warehouse.
        """
        from app.domain.services.fifo_discharge_service import FIFODischargeService
        fifo_service = FIFODischargeService()
        
        dest_company_id = await self.repository.get_warehouse_owner_id(to_warehouse_id)
        if not dest_company_id:
            raise ValueError(f"ERR_TRANSFER_TARGET_NOT_FOUND: Warehouse {to_warehouse_id} not found.")
        
        transit_warehouse_id = await self.repository.ensure_transit_warehouse(to_warehouse_id, dest_company_id)

        val_src = await self.repository.get_wac_valuation(product_id, from_warehouse_id, company_id)
        current_wac = val_src.wac if val_src else Money(Decimal("0.0"), "MXN")

        discharge_plan = await fifo_service.get_discharge_plan(
            inventory_repo=self.repository,
            product_id=product_id,
            warehouse_id=from_warehouse_id,
            requested_qty=quantity,
            company_id=company_id,
            strict=False,
            selected_batch_id=selected_batch_id
        )

        first_out_m = None
        for instr in discharge_plan:
            out_movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=from_warehouse_id,
                product_id=product_id,
                company_id=company_id,
                quantity=-instr.quantity_to_discharge,
                uom_id=uom_id,
                weight=weight * (instr.quantity_to_discharge / quantity),
                price=current_wac, 
                movement_type="OUT",
                document_type="TRANS_DISPATCH",
                document_id=transfer_id,
                source_movement_id=instr.source_movement_id,
                customs_pedimento_id=instr.customs_pedimento_id
            )
            await self.repository.record_movement(out_movement)
            
            if instr.source_movement_id:
                await self.repository.consume_movement_balance(
                    movement_id=instr.source_movement_id, 
                    quantity=instr.quantity_to_discharge
                )

            if not first_out_m:
                first_out_m = out_movement
        
        in_transit_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=transit_warehouse_id,
            product_id=product_id,
            company_id=dest_company_id,
            quantity=quantity,
            uom_id=uom_id,
            weight=weight,
            price=current_wac, 
            movement_type="IN",
            document_type="TRANS_IN_TRANSIT",
            document_id=transfer_id
        )
        await self.repository.record_movement(in_transit_movement, allow_negative=True)
        
        return first_out_m

    async def receive_transfer(
        self, 
        from_warehouse_id: uuid.UUID, 
        to_warehouse_id: uuid.UUID, 
        product_id: uuid.UUID, 
        quantity: Decimal, 
        uom_id: uuid.UUID, 
        weight: Decimal, 
        company_id: uuid.UUID, 
        transfer_id: uuid.UUID,
        location: Optional[str] = None,
        background_tasks: Optional[Any] = None
    ) -> MovementEntity:
        """
        [Phase 63] Laissez-Faire: Moves stock from IN_TRANSIT to final destination.
        Density Guard validation moved to BackgroundTask to ensure operational continuity.
        """
        if await self.repository.has_processed_document("TRANS_RECEIVE", transfer_id, company_id):
            return None 

        transit_warehouse_id = await self.repository.ensure_transit_warehouse(to_warehouse_id, company_id)

        val_transit = await self.repository.get_wac_valuation(product_id, transit_warehouse_id, company_id)
        transit_wac = val_transit.wac if val_transit else Money(Decimal("0.0"), "MXN")

        out_transit_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=transit_warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=-quantity,
            uom_id=uom_id,
            weight=weight,
            price=transit_wac,
            movement_type="OUT",
            document_type="TRANS_RECV_TRANSIT",
            document_id=transfer_id
        )
        await self.repository.record_movement(out_transit_movement, allow_negative=True)
        
        in_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=to_warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=quantity,
            uom_id=uom_id,
            weight=weight,
            price=transit_wac,
            movement_type="IN",
            document_type="TRANS_RECEIVE",
            document_id=transfer_id,
            location=location
        )
        # Fast-Track (Anexo 24 SSOT compliance)
        in_movement.validation_status = "PENDING"
        await self.repository.record_movement(in_movement)
        
        # ─── Density Guard Audit (Asynchronous) ───
        if location and background_tasks:
            from app.services.density_guard_audit import run_density_guard_audit
            background_tasks.add_task(
                run_density_guard_audit,
                warehouse_id=to_warehouse_id,
                location_code=location,
                quantity_moved=quantity,
                movement_id=in_movement.id,
                company_id=company_id,
                repository=self.repository
            )
            logger.info(f"[Phase 63] Queued background audit for location {location}")
        
        return in_movement
