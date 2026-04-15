import uuid
import asyncio
from datetime import datetime, timedelta, timezone
import logging
from decimal import Decimal
from typing import List

logger = logging.getLogger(__name__)

from app.domain.repositories.inventory_repository import IInventoryRepository
from app.domain.interfaces.master_data_client import IMasterDataClient
from app.schemas.dashboard import DashboardDTO, ValuationSummary
from app.domain.entities.inventory_item import HourlyMovementEntity

class GetInventoryDashboardHandler:
    def __init__(self, repo: IInventoryRepository, md_client: IMasterDataClient):
        self.repo = repo
        self.md_client = md_client

    async def execute(self, warehouse_id: uuid.UUID, company_id: uuid.UUID, trace_id: str = None) -> DashboardDTO:
        # 1. Sequential Orchestration: Repo Telemetry + Basic Stock List for Variation
        # We MUST NOT use asyncio.gather here because the repository uses a single SQLAlchemy session,
        # and concurrent queries on the same session are not allowed.
        telemetry = await self.repo.get_dashboard_telemetry(warehouse_id, company_id)
        levels = await self.repo.get_inventory_levels(company_id)
        
        # We need the total current stock to back-calculate variation
        current_total_stock = Decimal(sum(l.quantity for l in levels if l.warehouse_id == warehouse_id) or 0)

        # 2. Parallel Enrichment: Master Data calls for Alerts
        enrichment_tasks = [
            self.md_client.get_product_internal_metadata(alert.product_id, company_id, trace_id)
            for alert in telemetry.alerts
        ]
        
        metadata_results = []
        try:
            # Use return_exceptions=True to handle partial failures in Master Data service
            results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            for alert, res in zip(telemetry.alerts, results):
                if isinstance(res, Exception):
                    logger.error(f"MD Enrichment failed for {alert.product_id}: {str(res)}")
                    metadata_results.append({"sku": alert.sku, "name": "Material (Metadata Offline)"})
                else:
                    metadata_results.append(res)
        except Exception as e:
            logger.error(f"Critical failure in telemetry enrichment: {str(e)}")
            metadata_results = [{"sku": alert.sku, "name": "N/A"} for alert in telemetry.alerts]
        
        # Apply metadata to alerts
        for alert, metadata in zip(telemetry.alerts, metadata_results):
            alert.sku = metadata.get("sku", alert.sku)
            alert.name = metadata.get("name", "Material Industrial")

        # 3. Variation Engine (Back-calculation)
        total_in_24h = sum(h.entries for h in telemetry.hourly_series)
        total_out_24h = sum(h.exits for h in telemetry.hourly_series)
        
        # stock_today = stock_yesterday + entries - exits
        # stock_yesterday = stock_today - entries + exits
        stock_yesterday = max(Decimal("0.0"), current_total_stock - total_in_24h + total_out_24h)
        
        variation_pct = Decimal("0.0")
        if stock_yesterday > 0:
            variation_pct = ((current_total_stock - stock_yesterday) / stock_yesterday) * Decimal("100.0")
        elif current_total_stock > 0:
            variation_pct = Decimal("100.0") # From 0 to something is 100% growth for dashboard purposes

        # 4. Gap Filling Strategy (Python Side)
        filled_series = self._fill_hourly_gaps(telemetry.hourly_series)

        return DashboardDTO(
            valuation=ValuationSummary(
                total_usd=telemetry.valuation_total,
                variation_percentage=variation_pct.quantize(Decimal("0.01")),
                stock_yesterday=stock_yesterday,
                current_total_stock=current_total_stock
            ),
            critical_alerts=telemetry.alerts,
            movement_series=filled_series,
            recent_activity=telemetry.recent_movements,
            meta={
                "trace_id": trace_id,
                "warehouse_id": str(warehouse_id),
                "server_time": datetime.now(timezone.utc).isoformat()
            }
        )

    async def execute_consolidated(self, company_id: uuid.UUID, trace_id: str = None) -> List[DashboardDTO]:
        """
        Orchestrates telemetry collection for all company warehouses.
        Sequential execution per warehouse to respect SQLAlchemy session constraints.
        """
        # 1. Get all local warehouses
        warehouses = await self.repo.list_warehouses(company_id)
        
        if not warehouses:
            logger.warning(f"CONSOLIDATED_DASHBOARD: No warehouses found for company {company_id}")
            return []

        # 2. Sequential execution (SQLAlchemy sessions are NOT thread-safe for parallel queries)
        results = []
        for wh in warehouses:
            try:
                data = await self.execute(wh.id, company_id, trace_id)
                results.append(data)
            except Exception as e:
                logger.error(f"Failed to fetch telemetry for Wh {wh.id}: {str(e)}")
        
        return results

    def _fill_hourly_gaps(self, series: List[HourlyMovementEntity]) -> List[HourlyMovementEntity]:
        """
        Ensures a continuous 24h series for frontend charts.
        Handles timezone-aware comparisons between DB results and generated hours.
        """
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        
        # Ensure series hours are aware or treated as UTC
        series_map = {}
        for s in series:
            h = s.hour
            if h.tzinfo is None:
                h = h.replace(tzinfo=timezone.utc)
            series_map[h.replace(minute=0, second=0, microsecond=0)] = s
        
        filled = []
        for i in range(24):
            hour_to_check = now - timedelta(hours=i)
            if hour_to_check in series_map:
                filled.append(series_map[hour_to_check])
            else:
                filled.append(HourlyMovementEntity(
                    hour=hour_to_check,
                    entries=Decimal("0.0"),
                    exits=Decimal("0.0")
                ))
        
        # Return sorted by time ascending
        return sorted(filled, key=lambda x: x.hour)
