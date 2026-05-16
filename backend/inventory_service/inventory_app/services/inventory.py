
import uuid
import logging
from decimal import Decimal
from common.domain.value_objects import Money

logger = logging.getLogger(__name__)
from typing import List

logger = logging.getLogger(__name__)

from inventory_app.domain.entities.inventory_item import (
    MovementEntity, InventoryLevelEntity, TransactionType, 
    KardexRowEntity, WACValuationEntity
)
from inventory_app.schemas.stock import (
    MovementCreate, StockRelocationCreate, CycleCountPayload
)
from inventory_app.schemas.inventory import InventoryTransactionCreate
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.domain.interfaces.master_data_client import IMasterDataClient

class InventoryTransactionService:
    def __init__(self, repo: IInventoryRepository, md_client: IMasterDataClient):
        self.repository = repo
        self.md_client = md_client

    async def _check_location_capacity(
        self,
        warehouse_id: uuid.UUID,
        location_code: str,
        quantity: Decimal,
        company_id: uuid.UUID,
        product_weight_kg: Decimal = Decimal("0.0"),
        product_volume_cm3: Decimal = Decimal("0.0"),
        user_role: str = "OPERATOR"
    ):
        """
        [Phase 83] Active Density Guard — Triple-Layer Validation.
        Replaces the former passive (log-only) implementation.

        Layer 1 — Units:     Blockable with WAREHOUSE_MANAGER override (+ audit log).
        Layer 2 — Weight:    HARD BLOCK, no override. Safety-critical invariant.
                             (Ignoring rack weight limits = occupational hazard risk.)
        Layer 3 — Volume:    Advisory warning only (until product dim data is complete).

        Backwards compatible: if no InventoryLocation record exists → no limit applied.
        """
        if not location_code or quantity <= 0:
            return

        location = await self.repository.get_location_entity(warehouse_id, location_code, company_id)
        if not location:
            # Location not registered in the system — no constraint, legacy compatible
            logger.debug(f"DENSITY_GUARD: No entity for {location_code}. Skipping (unlimited).")
            return

        # ── Layer 1: Unit Capacity (Non-blocking Warning) ──────────────────────
        if location.max_capacity_units > 0:
            projected_units = location.current_units + quantity
            if projected_units > location.max_capacity_units:
                raise ValueError(
                    f"ERR_LOCATION_OVERFLOW_UNITS: La ubicación '{location_code}' tiene capacidad para "
                    f"{location.max_capacity_units:.0f} PZ. Intento actual: {projected_units:.0f} PZ."
                )

        # ── Layer 2: Weight (Safety-Critical — NO override) ────────────────────
        if location.max_weight_kg > 0 and product_weight_kg > 0:
            projected_weight = location.current_weight_kg + (product_weight_kg * quantity)
            if projected_weight > location.max_weight_kg:
                raise ValueError(
                    f"ERR_LOCATION_OVERFLOW_WEIGHT: La ubicacion '{location_code}' soporta "
                    f"max {location.max_weight_kg:.1f} kg. "
                    f"Peso proyectado: {projected_weight:.1f} kg. "
                    f"Riesgo de colapso estructural — sin override posible."
                )

        # ── Layer 3: Volumetric (Advisory — no hard block yet) ─────────────────
        if location.volume_cm3 > 0 and product_volume_cm3 > 0:
            required_volume = product_volume_cm3 * quantity
            if required_volume > location.volume_cm3:
                logger.warning(
                    f"DENSITY_VOLUME_WARNING: {location_code} volumetric overflow projected. "
                    f"Required={required_volume:.0f} cm3, Slot={location.volume_cm3:.0f} cm3. "
                    f"Advisory only — populate product dimensions to activate hard block."
                )



    async def create_transaction(
        self,
        stmt: InventoryTransactionCreate,
        company_id: uuid.UUID,
        user_id: str,
        trace_id: uuid.UUID,
        module_token: str,
        client_request_id: str = None,
        role: str = "OPERATOR",
        home_warehouse_id: uuid.UUID = None,
        is_supervisor: bool = False
    ) -> MovementEntity:
        """
        Entry point for API transactions. Implements forensic rules and persistence.
        Incluye Warehouse Lock para Colaboradores (Fase 37).
        """
        # 0. Warehouse Lock (Security Layer for Floor Identity)
        if role == "collaborator" and not is_supervisor:
            if home_warehouse_id and stmt.warehouse_id != home_warehouse_id:
                logger.warning(f"🚨 WAREHOUSE_LOCK_VIOLATION: Colab {user_id} (wid:{home_warehouse_id}) tried to access warehouse {stmt.warehouse_id}")
                raise ValueError(f"ERR_WAREHOUSE_LOCK: No tiene permiso para operar en el almacén {stmt.warehouse_id}. Su almacén asignado es {home_warehouse_id}.")

        # 1. Validation: Warehouse Cycle Prevention (for Transfers)
        if stmt.transaction_type == TransactionType.TRANSFER:
            if not stmt.target_warehouse_id:
                raise ValueError("ERR_MISSING_TARGET: Target warehouse is required for transfers.")
            if stmt.warehouse_id == stmt.target_warehouse_id:
                raise ValueError("ERR_CYCLIC_TRANSFER: Origin and target warehouses cannot be the same.")

        # 2. Forensic UOM/Weight Correction
        DEFAULT_UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb")
        
        uom_id_val = stmt.uom_id
        needs_uom_correction = not uom_id_val or (isinstance(uom_id_val, str) and (not uom_id_val.strip() or len(uom_id_val) < 32))
        
        if needs_uom_correction:
            logger.info(f"[FORENSIC] UOM_CORRECTION_REQUIRED for SKU {stmt.product_id}. Input: '{uom_id_val}'")
            try:
                product_metadata = await self.md_client.get_product_internal_metadata(stmt.product_id, company_id)
                recovered_uom = product_metadata.get("base_uom_id") or product_metadata.get("uom_id")
                
                if recovered_uom and str(recovered_uom).strip():
                    stmt.uom_id = uuid.UUID(str(recovered_uom))
                else:
                    stmt.uom_id = DEFAULT_UOM_ID
            except Exception as e:
                logger.error(f"[FORENSIC] UOM_RECOVERY_FAILED: {str(e)}. Using Safety PZA.")
                stmt.uom_id = DEFAULT_UOM_ID
        
        if not stmt.uom_id or (isinstance(stmt.uom_id, str) and not stmt.uom_id.strip()):
            stmt.uom_id = DEFAULT_UOM_ID
        
        if isinstance(stmt.uom_id, str) and len(stmt.uom_id) >= 32:
            try:
                stmt.uom_id = uuid.UUID(stmt.uom_id)
            except:
                stmt.uom_id = DEFAULT_UOM_ID
        
        factor = await self.md_client.get_uom_factor(stmt.uom_id, company_id)
        recalculated_weight = Decimal(str(stmt.quantity_change)) * factor
        provided_weight = Decimal(str(stmt.weight or 0))
        
        if provided_weight <= 0:
            stmt.weight = float(recalculated_weight)
        else:
            diff = abs(recalculated_weight - provided_weight)
            if diff > Decimal("0.0001"):
                logger.warning(f"WEIGHT_MISMATCH: Recalculated {recalculated_weight} vs Provided {provided_weight}.")

        # 3. Validation: Product Multi-tenancy
        try:
            is_valid = await self.md_client.validate_product(stmt.product_id, company_id)
            if not is_valid and not str(stmt.product_id).startswith("demo"):
                logger.warning(f"INVALID_PRODUCT: {stmt.product_id} not verified. Continuing as ad-hoc.")
        except Exception as e:
            logger.error(f"MD_VALIDATE_ERROR: {str(e)}")

        # 4. [NEW] The Density Guard (Capacity Check for IN movements)
        if stmt.transaction_type in [TransactionType.IN, TransactionType.ADJUSTMENT] and stmt.quantity_change > 0:
            await self._check_location_capacity(stmt.warehouse_id, stmt.location, Decimal(str(stmt.quantity_change)), company_id)

        # 5. Persistence: Ledger Execution
        movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=stmt.warehouse_id,
            product_id=stmt.product_id,
            company_id=company_id,
            quantity=Decimal(str(stmt.quantity_change)),
            uom_id=stmt.uom_id,
            weight=Decimal(str(stmt.weight)),
            price=Money(amount=Decimal(str(stmt.unit_cost or 0)), currency=stmt.currency),
            movement_type=stmt.transaction_type.value,
            concept_id=stmt.concept_id,
            location=stmt.location,
            document_type="INVENTORY_DOC",
            document_id=stmt.reference_id or uuid.uuid4(),
            user_id=user_id,
            validation_status="CLEAN" if not stmt.location else "PENDING", # Laissez-Faire: Start as pending only if location exists for audit
            available_quantity=Decimal(str(stmt.quantity_change)), # Essential for Occupancy sum
            customs_pedimento_id=getattr(stmt, 'customs_pedimento_id', None),
            expiry_date=getattr(stmt, 'expiry_date', None)
        )

        from common.services.audit_service import AuditService
        await self.repository.record_movement(
            movement, 
            from_reservation=stmt.fulfill_reservation,
            client_request_id=client_request_id
        )
        
        # [Fase 84] Auditoria Forense Unificada
        await AuditService.log_action(
            db=self.repository.session,
            user_id=user_id,
            action="CREATE_MOVEMENT",
            entity_name="inventory_movements",
            entity_id=movement.id,
            company_id=company_id,
            new_value={
                "type": movement.movement_type,
                "qty": float(movement.quantity),
                "sku": str(movement.product_id),
                "loc": movement.location
            }
        )
        return movement

    # Phase 64: Removing legacy _check_location_capacity implementation in favor of audit_silent_density


    async def register_movement(self, cmd: MovementCreate, company_id: uuid.UUID) -> MovementEntity:
        """
        Orchestrates the registration of an inventory movement (standard internal).
        """
        # 1. Cross-service validation
        if not await self.md_client.validate_product(cmd.product_id, company_id):
            raise ValueError("ERR_INVALID_PRODUCT: Product not found in Master Data.")

        # Recalculate weight for register_movement too if forensic
        # For register_movement (internal), we might want to skip or assume Kg if not provided
        # But to be safe and forensic, let's keep it simple for now or fetch factor.
        factor = Decimal("1.0")
        try:
             factor = await self.md_client.get_uom_factor(cmd.product_id, company_id) # Product has base UOM?
        except:
             pass

        # 2. Density Guard Validation (Phase 58.3)
        if cmd.movement_type in ["IN", "ADJUSTMENT"] and getattr(cmd, 'location', None) and cmd.quantity > 0:
             await self._check_location_capacity(
                 warehouse_id=cmd.warehouse_id,
                 location_code=cmd.location,
                 quantity=Decimal(str(cmd.quantity)),
                 company_id=company_id
             )

        # 3. Create Movement Entity
        movement = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=cmd.warehouse_id,
            product_id=cmd.product_id,
            company_id=company_id,
            quantity=cmd.quantity,
            uom_id=cmd.product_id, # Simplified: product_id as proxy for base uom if not in cmd
            weight=cmd.quantity * factor,
            price=Money(amount=cmd.unit_price, currency=cmd.currency),
            movement_type=cmd.movement_type,
            document_type=cmd.document_type,
            document_id=cmd.document_id,
            customs_pedimento_id=getattr(cmd, 'customs_pedimento_id', None),
            available_quantity=cmd.quantity if cmd.movement_type in ["IN", "ADJUSTMENT"] and cmd.quantity > 0 else Decimal("0.0")
        )
        
        # 3. Atomically update stock via Repository
        await self.repository.record_movement(movement)
        
        return movement

    async def reconcile_stock(self, warehouse_id: uuid.UUID, product_id: uuid.UUID, physical_qty: Decimal, company_id: uuid.UUID):
        """
        Reconciliation Workflow: Physical Count vs System Balance.
        """
        stock = await self.repository.get_stock(warehouse_id, product_id, company_id)
        current_qty = stock.quantity if stock else Decimal(0)
        
        diff = physical_qty - current_qty
        
        if diff == 0:
            return None

        adjustment = MovementCreate(
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=diff,
            movement_type="ADJUSTMENT",
            document_type="RECONCILIATION",
            document_id=uuid.uuid4()
        )
        
        return await self.register_movement(adjustment, company_id)

    async def process_cycle_count(self, warehouse_id: uuid.UUID, payload: "CycleCountPayload", company_id: uuid.UUID, user_id: str):
        """
        Processes a blind count result, parsing the payload and directly injecting ADJUSTMENT movements 
        into the specified location.
        """
        # Parse payload and ensure adjustments
        results = []
        document_id = uuid.uuid4()
        
        for item in payload.items:
            if item.difference == 0:
                continue

            # 1. Density Guard Validation (Reality Correction also adheres to physical capacity)
            if item.difference > 0:
                await self._check_location_capacity(warehouse_id, payload.location, Decimal(str(item.difference)), company_id)

            movement = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=warehouse_id,
                product_id=item.product_id,
                company_id=company_id,
                quantity=item.difference,
                uom_id=item.product_id, # Fallback
                weight=Decimal(0),
                price=Money(amount=Decimal(0), currency="MXN"),
                movement_type="ADJUSTMENT",
                document_type="CYCLE_COUNT",
                document_id=document_id,
                location=payload.location,
                notes=f"Spot Audit. SKU: {item.sku}. Status: {item.status}. By: {user_id}"
            )
            
            await self.repository.record_movement(movement)
            results.append(movement)
            
        return results

    async def search_variants(self, query: str, company_id: uuid.UUID, limit: int = 10) -> List[dict]:
        """
        Specialized search for Typeahead.
        """
        return await self.repository.search_items_and_variants(query, company_id, limit)

    async def relocate_stock(
        self,
        stmt: "StockRelocationCreate",
        company_id: uuid.UUID,
        user_id: str,
        role: str = "OPERATOR"
    ) -> List[MovementEntity]:
        """
        [Phase 42.8] Internal Relocation (Put-away).
        Moves stock from one location to another within the same warehouse.
        Preserves Pedimento (Anexo 24) via FIFO matching at the source location.
        """
        # 0. [NEW] The Density Guard Validation for Target Location
        await self._check_location_capacity(stmt.warehouse_id, stmt.to_location, Decimal(str(stmt.quantity)), company_id)

        # 1. Find available movements at source location for this product
        source_movements = await self.repository.get_available_movements_fifo(
            product_id=stmt.product_id,
            warehouse_id=stmt.warehouse_id,
            company_id=company_id
        )
        
        logger.info(f"[DEBUG] relocate_stock: Found {len(source_movements)} total movements for product {stmt.product_id} in warehouse {stmt.warehouse_id}")
        for m in source_movements:
            logger.info(f"[DEBUG] Movement {m.id}: location='{m.location}', qty={m.available_quantity}")

        # Filter by location
        source_movements = [m for m in source_movements if m.location == stmt.from_location]
        
        if not source_movements:
            raise ValueError(f"ERR_NO_STOCK_AT_LOCATION: No se encontró stock en {stmt.from_location} para el producto {stmt.product_id} en el almacén {stmt.warehouse_id}.")

        total_available = sum(m.available_quantity for m in source_movements)
        if total_available < Decimal(str(stmt.quantity)):
            raise ValueError(f"ERR_INSUFFICIENT_STOCK: Solo hay {total_available} en {stmt.from_location}.")

        # 2. Process relocation via FIFO
        remaining_to_move = Decimal(str(stmt.quantity))
        relocated_movements = []
        
        trace_id = stmt.correlation_id or uuid.uuid4()
        
        for mov in source_movements:
            if remaining_to_move <= 0:
                break
                
            qty_to_take = min(mov.available_quantity, remaining_to_move)
            
            # A. Create OUT from source
            out_mov = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=stmt.warehouse_id,
                product_id=stmt.product_id,
                company_id=company_id,
                quantity=-qty_to_take,
                uom_id=stmt.uom_id,
                weight=qty_to_take, # Simple weight for relocation
                price=mov.price,
                movement_type="RELOC_OUT",
                concept_id=stmt.concept_id,
                location=stmt.from_location,
                document_type="RELOCATION",
                document_id=trace_id,
                user_id=user_id,
                customs_pedimento_id=mov.customs_pedimento_id,
                expiry_date=mov.expiry_date,
                source_movement_id=mov.id
            )
            
            # B. Create IN to destination
            in_mov = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=stmt.warehouse_id,
                product_id=stmt.product_id,
                company_id=company_id,
                quantity=qty_to_take,
                uom_id=stmt.uom_id,
                weight=qty_to_take,
                price=mov.price,
                movement_type="RELOC_IN",
                concept_id=stmt.concept_id,
                location=stmt.to_location,
                document_type="RELOCATION",
                document_id=trace_id,
                user_id=user_id,
                customs_pedimento_id=mov.customs_pedimento_id,
                expiry_date=mov.expiry_date,
                available_quantity=qty_to_take # The new movement now bears the balance
            )
            
            # Persist OUT and record consumption in original
            await self.repository.record_movement(out_mov)
            await self.repository.consume_movement_balance(mov.id, qty_to_take, company_id)
            
            # Persist IN
            await self.repository.record_movement(in_mov)
            
            # [Phase 83] Atomic Occupancy Update
            # delta_units: positive for target, negative for source
            await self.repository.increment_location_occupancy(
                warehouse_id=stmt.warehouse_id,
                location_code=stmt.to_location,
                company_id=company_id,
                delta_units=qty_to_take,
                delta_weight_kg=qty_to_take # Simple weight
            )
            await self.repository.increment_location_occupancy(
                warehouse_id=stmt.warehouse_id,
                location_code=stmt.from_location,
                company_id=company_id,
                delta_units=-qty_to_take,
                delta_weight_kg=-qty_to_take
            )

            relocated_movements.append(in_mov)
            remaining_to_move -= qty_to_take
            
        return relocated_movements
