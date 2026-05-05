from decimal import Decimal
import uuid
import logging
from typing import List, Optional
from wms_app.domain.interfaces.inventory_client import IInventoryClient
from wms_app.domain.repositories.item_repository import IItemRepository
from wms_app.domain.entities.item import ItemEntity
from wms_app.schemas.inventory import MasterDataSyncPayload, SyncResult

logger = logging.getLogger(__name__)

class WMSSyncService:
    def __init__(self, item_repo: IItemRepository, inventory_client: IInventoryClient):
        self.repo = item_repo
        self.inventory_client = inventory_client

    async def sync_initial_data(
        self, company_id: uuid.UUID, payload: MasterDataSyncPayload, token: str
    ) -> SyncResult:
        """
        Syncs metadata and initial stock for items based on Master Data payload.
        Zero infrastructure leaks (SQLAlchemy/Models removed).
        """
        created_count = 0
        updated_count = 0
        processed_count = 0
        
        for product in payload.products:
            for version in product.versions:
                processed_count += 1
                
                # Fetch existing entity via repository
                item = await self.repo.get_by_sku(
                    company_id=company_id, 
                    sku=product.sku, 
                    version_number=version.version_number
                )

                if item:
                    item.name = product.name
                    item.master_product_id = product.id
                    updated_count += 1
                else:
                    item = ItemEntity(
                        id=uuid.uuid4(),
                        company_id=company_id,
                        code=product.sku, # Code used as SKU for now
                        name=product.name,
                        sku=product.sku,
                        version_number=version.version_number,
                        stock_quantity=Decimal("0.0"),
                        master_product_id=product.id
                    )
                    created_count += 1

                # Sync real stock from Inventory Service
                try:
                    resp = await self.inventory_client.get_stock(company_id=company_id, token=token)
                    stock_data = resp.get("data", []) if isinstance(resp, dict) else []
                    p_stock = next((s for s in stock_data if uuid.UUID(str(s["product_id"])) == product.id), None)
                    if p_stock:
                        item.stock_quantity = Decimal(str(p_stock["total_quantity"]))
                except Exception as e:
                    logger.warning(f"Could not sync stock for {product.sku}: {e}")

                # Save entity via repository
                await self.repo.save(item)
        
        return SyncResult(processed=processed_count, created=created_count, updated=updated_count)
