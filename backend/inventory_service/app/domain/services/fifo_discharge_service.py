import uuid
import logging
from decimal import Decimal
from typing import List, NamedTuple, Optional
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.entities.inventory_item import MovementEntity

logger = logging.getLogger(__name__)

class DischargeInstruction(NamedTuple):
    source_movement_id: uuid.UUID
    quantity_to_discharge: Decimal
    customs_pedimento_id: Optional[uuid.UUID]

class FIFODischargeService:
    """
    Expert service to calculate Anexo 24 FIFO discharge increments.
    Identifies which inbound movements (with positive balance) should be consumed.
    """

    @staticmethod
    async def get_discharge_plan(
        inventory_repo: IInventoryRepository,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        requested_qty: Decimal,
        company_id: uuid.UUID,
        strict: bool = True,
        selected_batch_id: Optional[uuid.UUID] = None
    ) -> List[DischargeInstruction]:
        """
        Calculates the list of source movements and quantities to fulfill a requested 'OUT'.
        Uses FIFO (First-In, First-Out) based on the Customs Date or Created At.
        If selected_batch_id is provided, it prioritizes that specific batch regardless of FIFO.
        If strict=False, it allows fulfilling the deficit with a 'Virtual' instruction.
        """
        
        # 1. Fetch available stock-bearing movements via Repository (Decoupled from ORM)
        available_movements = await inventory_repo.get_available_movements_fifo(
            product_id=product_id,
            warehouse_id=warehouse_id,
            company_id=company_id
        )
        
        # 2. Prioritize Selected Batch if provided
        if selected_batch_id:
            # Reorder movements to put the selected batch at the top
            selected = [m for m in available_movements if str(m.id) == str(selected_batch_id)]
            others = [m for m in available_movements if str(m.id) != str(selected_batch_id)]
            available_movements = selected + others
            
            if not selected:
                logger.warning(f"[FIFO] Selected batch {selected_batch_id} not found or has no balance. Falling back to FIFO.")

        instructions: List[DischargeInstruction] = []
        remaining_to_fulfill = requested_qty
        
        for m in available_movements:
            if remaining_to_fulfill <= 0:
                break
                
            can_take = min(m.available_quantity, remaining_to_fulfill)
            
            instructions.append(DischargeInstruction(
                source_movement_id=m.id,
                quantity_to_discharge=can_take,
                customs_pedimento_id=m.customs_pedimento_id
            ))
            
            remaining_to_fulfill -= can_take
            
        if remaining_to_fulfill > 0:
            if not strict:
                # 🛡️ Ghost Stock Fulfillment (Phase 42.0 - Local Transfers)
                # We fulfill the remaining with a virtual movement (no source, no pedimento)
                instructions.append(DischargeInstruction(
                    source_movement_id=None,
                    quantity_to_discharge=remaining_to_fulfill,
                    customs_pedimento_id=None
                ))
                logger.info(f"[FIFO] Fulfilling {remaining_to_fulfill} units via GHOST_STOCK for non-binational transfer.")
            else:
                # 🛡️ Ghost Stock Protection (Anexo 24 - Binational)
                from common.exceptions import BusinessRuleException
                raise BusinessRuleException(
                    message=f"ERR_LEGAL_STOCK_INSUFFICIENT: Insufficient legal stock with customs documentation for discharge. "
                            f"Missing {remaining_to_fulfill} units without assignable pedimento.",
                    details={
                        "requested": str(requested_qty),
                        "missing_legal_balance": str(remaining_to_fulfill),
                        "product_id": str(product_id),
                        "warehouse_id": str(warehouse_id)
                    }
                )
            
        return instructions
            
        return instructions
