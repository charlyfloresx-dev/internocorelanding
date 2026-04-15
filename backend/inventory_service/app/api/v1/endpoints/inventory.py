from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from decimal import Decimal

from fastapi.responses import StreamingResponse
import io
import csv
from datetime import datetime

from app.db.db import get_session
from app.services.inventory import InventoryService
from app.schemas.stock import StockRead, MovementCreate, StockReserveCmd, TransferDispatchCmd, TransferReceiveCmd, CycleCountPayload
from common.schemas import ApiResponse
from app.services.transfer_service import TransferService

router = APIRouter()

@router.get("/stock/{warehouse_id}/{product_id}", response_model=ApiResponse[StockRead])
async def get_stock(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    service = InventoryService(session)
    stock = await service.repository.get_stock(warehouse_id, product_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return ApiResponse(data=stock)

@router.post("/movements", response_model=ApiResponse)
async def create_movement(
    cmd: MovementCreate,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    service = InventoryService(session)
    try:
        movement = await service.register_movement(cmd, x_company_id)
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
    service = InventoryService(session)
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
    service = InventoryService(session)
    try:
        stock = await service.repository.reserve_stock(cmd.warehouse_id, cmd.product_id, cmd.quantity)
        return ApiResponse(message="Stock reserved successfully", data={"available_quantity": stock.available_quantity})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/release", response_model=ApiResponse)
async def release_inventory(
    cmd: StockReserveCmd,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    service = InventoryService(session)
    try:
        stock = await service.repository.release_stock(cmd.warehouse_id, cmd.product_id, cmd.quantity)
        return ApiResponse(message="Stock released successfully", data={"available_quantity": stock.available_quantity})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfers/dispatch", response_model=ApiResponse)
async def dispatch_transfer(
    cmd: TransferDispatchCmd,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    service = TransferService(session)
    try:
        movement = await service.dispatch_transfer(
            cmd.from_warehouse_id, cmd.to_warehouse_id, cmd.product_id, 
            cmd.quantity, x_company_id, cmd.transfer_id
        )
        return ApiResponse(message="Transfer dispatched successfully", data={"movement_id": movement.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfers/receive", response_model=ApiResponse)
async def receive_transfer(
    cmd: TransferReceiveCmd,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    service = TransferService(session)
    try:
        movement = await service.receive_transfer(
            cmd.from_warehouse_id, cmd.to_warehouse_id, cmd.product_id, 
            cmd.quantity, x_company_id, cmd.transfer_id
        )
        if not movement:
             return ApiResponse(message="Transfer already received", data={})
        return ApiResponse(message="Transfer received successfully", data={"movement_id": movement.id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/warehouses/{warehouse_id}/audit-export")
async def export_audit_sheet(
    warehouse_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    x_company_id: uuid.UUID = Header(...)
):
    from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
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
    from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
    from app.services.inventory import InventoryTransactionService
    
    repo = SQLAlchemyInventoryRepository(session, None)
    service = InventoryTransactionService(repo)
    
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
