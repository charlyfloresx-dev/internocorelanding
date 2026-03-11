from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from decimal import Decimal

from app.db.db import get_session
from app.services.inventory import InventoryService
from app.schemas.stock import StockRead, MovementCreate, StockReserveCmd, TransferDispatchCmd, TransferReceiveCmd
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
