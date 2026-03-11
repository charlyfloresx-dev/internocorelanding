from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.interfaces.master_data_client import IMasterDataClient
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.services.inventory import InventoryTransactionService
from app.dependencies.clients import get_master_data_client

async def get_inventory_repository(db: AsyncSession = Depends(get_db)) -> IInventoryRepository:
    return SQLAlchemyInventoryRepository(db)

async def get_inventory_service(
    repo: IInventoryRepository = Depends(get_inventory_repository),
    md_client: IMasterDataClient = Depends(get_master_data_client)
) -> InventoryTransactionService:
    return InventoryTransactionService(repo, md_client)
