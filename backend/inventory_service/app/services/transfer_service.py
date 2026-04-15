import uuid
from typing import Optional
from decimal import Decimal
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money


class TransferService:
    def __init__(self, repo: IInventoryRepository):
        self.repository = repo

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
        Supports both intra-company and inter-company transfers by fetching the destination owner.
        Propagates source WAC as unit_price for the destination.
        
        [PHASE 42.6] Enhanced with FIFO/Anexo 24 picking logic.
        """
        # 0. Expert logic imports for FIFO
        from app.domain.services.fifo_discharge_service import FIFODischargeService
        fifo_service = FIFODischargeService()
        
        # 1. Fetch Destination Warehouse to identify owner for Transit (Zero Trust compliance)
        dest_company_id = await self.repository.get_warehouse_owner_id(to_warehouse_id)
        if not dest_company_id:
            raise ValueError(f"ERR_TRANSFER_TARGET_NOT_FOUND: Warehouse {to_warehouse_id} not found.")
        
        # 2. Provision Transit Warehouse (owned by destination company)
        transit_warehouse_id = await self.repository.ensure_transit_warehouse(to_warehouse_id, dest_company_id)

        # 3. Get Source WAC to propagate value
        val_src = await self.repository.get_wac_valuation(product_id, from_warehouse_id, company_id)
        current_wac = val_src.wac if val_src else Money(Decimal("0.0"), "MXN")

        # 4. [NEW] Calculate FIFO Discharge Plan (Picking Recommendation)
        # Internal transfers are lenient (strict=False) unless otherwise configured.
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
        
        # 5. Record OUT movements for Each Batch found in FIFO plan
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
            
            # 5.1 Consume Balance in SQL (FIFO consumption)
            if instr.source_movement_id:
                await self.repository.consume_movement_balance(
                    movement_id=instr.source_movement_id, 
                    quantity=instr.quantity_to_discharge
                )

            if not first_out_m:
                first_out_m = out_movement
        
        # 6. IN to IN_TRANSIT virtual warehouse (One consolidated record for Transit Limbo)
        in_transit_movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=transit_warehouse_id,
            product_id=product_id,
            company_id=dest_company_id,
            quantity=quantity,
            uom_id=uom_id,
            weight=weight,
            price=current_wac, # Propagate value
            movement_type="IN",
            document_type="TRANS_IN_TRANSIT",
            document_id=transfer_id
        )
        await self.repository.record_movement(in_transit_movement, allow_negative=True)
        
        return first_out_m

    async def receive_transfer(self, from_warehouse_id: uuid.UUID, to_warehouse_id: uuid.UUID, product_id: uuid.UUID, quantity: Decimal, uom_id: uuid.UUID, weight: Decimal, company_id: uuid.UUID, transfer_id: uuid.UUID) -> MovementEntity:
        """
        Moves stock from IN_TRANSIT to final destination.
        Implements Idempotency to prevent double-receiving.
        """
        # 1. Idempotency Check: Already received?
        if await self.repository.has_processed_document("TRANS_RECEIVE", transfer_id, company_id):
            return None # Already processed
            
        # 2. Provision Transit Warehouse
        transit_warehouse_id = await self.repository.ensure_transit_warehouse(to_warehouse_id, company_id)

        # 3. Get Transit Valuation to propagate price
        # Transit belongs to the destination company
        val_transit = await self.repository.get_wac_valuation(product_id, transit_warehouse_id, company_id)
        transit_wac = val_transit.wac if val_transit else Money(Decimal("0.0"), "MXN")

        # 4. OUT from IN_TRANSIT
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
        
        # 5. IN to destination warehouse
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
            document_id=transfer_id
        )
        await self.repository.record_movement(in_movement)
        
        return in_movement
