from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_app.db.session import get_db
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.domain.interfaces.master_data_client import IMasterDataClient
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.services.variant_service import VariantService
from inventory_app.dependencies.clients import get_master_data_client

async def get_inventory_repository(
    db: AsyncSession = Depends(get_db),
    md_client: IMasterDataClient = Depends(get_master_data_client)
) -> IInventoryRepository:
    return SQLAlchemyInventoryRepository(db, md_client)

async def get_inventory_service(
    repo: IInventoryRepository = Depends(get_inventory_repository),
    md_client: IMasterDataClient = Depends(get_master_data_client)
) -> InventoryTransactionService:
    return InventoryTransactionService(repo, md_client)

async def get_variant_service(
    repo: IInventoryRepository = Depends(get_inventory_repository)
) -> VariantService:
    return VariantService(repo)
