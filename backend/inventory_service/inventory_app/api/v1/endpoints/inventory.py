from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from decimal import Decimal

from fastapi.responses import StreamingResponse
import io
import csv
from datetime import datetime

from inventory_app.db.session import get_db as get_session

from inventory_app.services.inventory import InventoryTransactionService as InventoryService
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.schemas.stock import StockRead, MovementCreate, StockReserveCmd, TransferDispatchCmd, TransferReceiveCmd, CycleCountPayload
from common.responses import ApiResponse
from inventory_app.services.transfer_service import TransferService
from common.infrastructure.websocket import manager

router = APIRouter()

@router.get("/stock/{warehouse_id}/{product_id}", response_model=ApiResponse[StockRead])
async def get_stock(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryService(repo, None)
    stock = await service.repository.get_stock(warehouse_id, product_id, x_company_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return ApiResponse(data=stock)

@router.post("/movements", response_model=ApiResponse)
async def create_movement(
    cmd: MovementCreate,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryService(repo, None)
    try:
        movement = await service.register_movement(cmd, x_company_id)
        
        # [Zero Polling] Broadcast real-time update
        await manager.broadcast_to_company(str(x_company_id), {
            "type": "INVENTORY_UPDATE",
            "company_id": str(x_company_id),
            "payload": {
                "id": str(movement.id),
                "folio": getattr(movement, 'folio', 'MOV-' + str(movement.id)[:6]),
                "concept_type": cmd.concept_type,
                "warehouse_id": str(cmd.warehouse_id),
                "created_at": datetime.utcnow().isoformat(),
                "created_by": "System"
            }
        })
        
        return ApiResponse(message="Movement recorded successfully", data={"id": movement.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reconcile", response_model=ApiResponse)
async def reconcile_inventory(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    physical_qty: Decimal,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryService(repo, None)
    try:
        adjustment = await service.reconcile_stock(warehouse_id, product_id, physical_qty, x_company_id)
        if not adjustment:
            return ApiResponse(message="Inventory is already in sync.")
        return ApiResponse(message="Inventory adjusted successfully", data={"adjustment_id": adjustment.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reserve", response_model=ApiResponse)
async def reserve_inventory(
    cmd: StockReserveCmd,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryService(repo, None)
    try:
        stock = await service.repository.reserve_stock(cmd.warehouse_id, cmd.product_id, cmd.quantity, x_company_id)
        return ApiResponse(message="Stock reserved successfully", data={"available_quantity": stock.available_quantity})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/release", response_model=ApiResponse)
async def release_inventory(
    cmd: StockReserveCmd,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryService(repo, None)
    try:
        stock = await service.repository.release_stock(cmd.warehouse_id, cmd.product_id, cmd.quantity, x_company_id)
        return ApiResponse(message="Stock released successfully", data={"available_quantity": stock.available_quantity})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfers/dispatch", response_model=ApiResponse)
async def dispatch_transfer(
    cmd: TransferDispatchCmd,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    repo = SQLAlchemyInventoryRepository(session)
    service = TransferService(repo)
    try:
        movement = await service.dispatch_transfer(
            cmd.from_warehouse_id, cmd.to_warehouse_id, cmd.product_id, 
            cmd.quantity, x_company_id, cmd.transfer_id
        )
        return ApiResponse(message="Transfer dispatched successfully", data={"movement_id": movement.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfers/receive", response_model=ApiResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_transfer(
    cmd: TransferReceiveCmd,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    """
    [Phase 63] Laissez-Faire Reception: Registers stock immediately.
    Density Guard validation moved to background.
    """
    repo = SQLAlchemyInventoryRepository(session)
    service = TransferService(repo)
    try:
        movement = await service.receive_transfer(
            from_warehouse_id=cmd.from_warehouse_id, 
            to_warehouse_id=cmd.to_warehouse_id, 
            product_id=cmd.product_id, 
            quantity=cmd.quantity, 
            company_id=x_company_id, 
            transfer_id=cmd.transfer_id,
            location=cmd.location,
            background_tasks=background_tasks
        )
        if not movement:
             return ApiResponse(message="Transfer already received", data={})
        
        # [Zero Polling] Broadcast real-time update
        await manager.broadcast_to_company(str(x_company_id), {
            "type": "INVENTORY_UPDATE",
            "company_id": str(x_company_id),
            "payload": {
                "id": str(movement.id),
                "folio": "TRF-REC-" + str(movement.id)[:6],
                "concept_type": "ENTRADA",
                "warehouse_id": str(cmd.to_warehouse_id),
                "created_at": datetime.utcnow().isoformat(),
                "created_by": "System"
            }
        })

        return ApiResponse(
            message="Transfer reception initiated (Laissez-Faire)", 
            data={"movement_id": movement.id, "status": "QUEUED_FOR_AUDIT"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/warehouses/{warehouse_id}/audit-export")
async def export_audit_sheet(
    warehouse_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
    repo = SQLAlchemyInventoryRepository(session, None)
    
    # [Zero Trust] Validate warehouse ownership
    await repo._validate_warehouse_ownership(warehouse_id, x_company_id)
    
    data = await repo.get_detailed_stock_report(warehouse_id, x_company_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Technical Header for the auditor
    writer.writerow(['Ubicacion', 'SKU', 'Descripcion', 'Pedimento', 'Teorico', 'Fisico_Check (Escribe aqui)'])
    
    for item in data:
        writer.writerow([
            item["location"],
            item["sku"],
            item["description"],
            item["pedimento"],
            item["quantity"],
            ""  # Space for manual count
        ])
    
    filename = f"Audit_Sheet_{warehouse_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/warehouses/{warehouse_id}/cycle-count", status_code=201)
async def submit_cycle_count(
    warehouse_id: uuid.UUID,
    payload: CycleCountPayload,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...),
    x_user_id: str = Header(default="unknown")
):
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryService(repo, None)
    
    try:
        results = await service.process_cycle_count(
            warehouse_id=warehouse_id,
            payload=payload,
            company_id=x_company_id,
            user_id=x_user_id
        )
        return {"status": "success", "adjustments_processed": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error de persistencia (Cycle Count)")
