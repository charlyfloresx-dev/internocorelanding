import uuid
from decimal import Decimal
from sqlalchemy import event, select, inspect, cast
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # ✅ Crucial para el cast
from common.exceptions import BusinessRuleException

from typing import Any, List, Optional
# Imports absolutos
from .inventory_document import InventoryDocument, DocumentStatus
from .inventory_movement import InventoryMovement
from .inventory_snapshot import InventorySnapshot

# ... (Eventos de inmutabilidad iguales)

def update_stock_and_cost(doc: Any, connection, reverse: bool):
    """
    Core Ledger logic optimizada para UUIDs nativos.
    """
    for mov in doc.movements:
        # 1. Fetch current snapshot metadata
        stmt = (
            select(
                InventorySnapshot.id,
                InventorySnapshot.quantity_on_hand,
                InventorySnapshot.average_cost
            )
            .where(
                InventorySnapshot.company_id == doc.company_id,
                InventorySnapshot.product_id == mov.product_id,
                InventorySnapshot.warehouse_id == mov.warehouse_id
            )
        )
        
        row = connection.execute(stmt).fetchone()
        
        if not row:
            # ✅ Usamos UUID real, no string
            new_id = uuid.uuid4() 
            connection.execute(
                InventorySnapshot.__table__.insert().values(
                    id=new_id,
                    company_id=doc.company_id,
                    product_id=mov.product_id,
                    warehouse_id=mov.warehouse_id,
                    quantity_on_hand=Decimal("0.0"),
                    average_cost=Decimal("0.0"),
                    created_at=doc.created_at or doc.updated_at,
                    is_active=True, # ✅ No olvidar campos base
                    version_id=1
                )
            )
            old_stock = Decimal("0.0")
            old_cost = Decimal("0.0")
            snapshot_id = new_id
        else:
            snapshot_id, old_stock, old_cost = row
            # Asegurar Decimal para evitar errores de punto flotante
            old_stock = Decimal(str(old_stock))
            old_cost = Decimal(str(old_cost))

        mov_qty = Decimal(str(mov.quantity))
        mov_cost = Decimal(str(mov.unit_cost))

        # Cálculo de stock
        new_stock = old_stock + (mov_qty if not reverse else -mov_qty)
        new_cost = old_cost

        # Lógica de Costo Promedio (Solo en entradas reales, no reversiones)
        if not reverse and mov_qty > 0:
            total_qty = old_stock + mov_qty
            if total_qty > 0:
                new_cost = ((old_stock * old_cost) + (mov_qty * mov_cost)) / total_qty

        # 2. Update via connection con snapshot_id como UUID
        connection.execute(
            InventorySnapshot.__table__.update()
            .where(InventorySnapshot.id == snapshot_id)
            .values(
                quantity_on_hand=new_stock,
                average_cost=new_cost,
                updated_at=doc.updated_at
            )
        )