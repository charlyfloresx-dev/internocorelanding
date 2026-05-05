from fastapi import APIRouter
from .endpoints import inventory, sales_orders, documents, locations, transfers, sales

api_router = APIRouter()
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(sales_orders.router, prefix="/sales-orders", tags=["sales-orders"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
