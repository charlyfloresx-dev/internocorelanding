import uuid
from typing import Optional
from dataclasses import dataclass
from inventory_app.schemas.readiness import InventoryReadinessDto, InventoryReadinessStep
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.domain.interfaces.master_data_client import IMasterDataClient
from common.exceptions import UnauthorizedException

@dataclass
class GetCompanyInventoryReadinessQuery:
    company_id: uuid.UUID
    # The user_id or role can be passed to validate permissions, though checking readiness is typically safe for all roles
    user_id: Optional[uuid.UUID] = None

class GetCompanyInventoryReadinessHandler:
    def __init__(self, repository: IInventoryRepository, md_client: IMasterDataClient):
        self.repository = repository
        self.md_client = md_client

    async def handle(self, query: GetCompanyInventoryReadinessQuery) -> InventoryReadinessDto:
        # Cross-Tenant authorization check is presumed handled via API JWT parsing
        if not query.company_id:
            raise UnauthorizedException(message="company_id cannot be null for readiness check")

        # 1. Gather Telemetry/Onboarding Status
        # Ideally, we query Master Data for global catalogs (UOM, currency, default warehouse)
        # And Inventory Repository for local metadata (are there any documents/products already loaded?).
        # For MVP, we aggregate parameters from both dependencies.

        # Retrieve warehouse count (since movement logic relies on it)
        try:
            # Assume md_client has a method or we retrieve a basic dashboard telemetry that checks warehouse existence
            # As a conceptual pattern (per Clean Architecture MVP), we check Master Data readiness endpoint if it exists
            # Otherwise we simulate fetching boolean flags for required elements.
            has_uom_configured = await self._check_base_catalogs(query.company_id)
            has_active_warehouse = await self._check_warehouses(query.company_id)
            has_products = await self._check_products(query.company_id)
            has_base_currency = await self._check_currency_settings(query.company_id)
            
        except Exception as e:
            # Fallback defensively if Master Data is unreachable
            has_uom_configured = False
            has_active_warehouse = False
            has_products = False
            has_base_currency = False

        # 2. Construction of Audit Steps based on Requirements
        steps = [
            InventoryReadinessStep(
                task="Configuración de Almacén",
                is_completed=has_active_warehouse,
                action_link="/settings/warehouses",
                importance="Critical"
            ),
            InventoryReadinessStep(
                task="Catálogo de Unidades (UoM)",
                is_completed=has_uom_configured,
                action_link="/settings/catalogs/uom",
                importance="High"
            ),
            InventoryReadinessStep(
                task="Carga de Productos Base",
                is_completed=has_products,
                action_link="/inventory/products/new",
                importance="High"
            ),
            InventoryReadinessStep(
                task="Definición de Moneda y Precios",
                is_completed=has_base_currency,
                action_link="/settings/billing",
                importance="Critical"
            )
        ]

        # 3. Validation Logic for the Dashboard Gatekeeper
        is_ready = all(step.is_completed for step in steps if step.importance == "Critical")
        
        return InventoryReadinessDto(
            company_id=query.company_id,
            is_ready=is_ready,
            steps=steps
        )

    # ── Mocks / Stubs for retrieving specific metrics pending cross-service endpoint ──

    async def _check_base_catalogs(self, company_id: uuid.UUID) -> bool:
        """Query MasterData regarding UOMs configured for this company"""
        return await self.md_client.check_uom_readiness(company_id)

    async def _check_warehouses(self, company_id: uuid.UUID) -> bool:
        """Query if the local or remote DB has at least one active warehouse for the company"""
        warehouses = await self.md_client.list_warehouses(company_id)
        return len(warehouses) > 0

    async def _check_products(self, company_id: uuid.UUID) -> bool:
        """Check if any physical products are registered"""
        return await self.md_client.check_product_readiness(company_id)

    async def _check_currency_settings(self, company_id: uuid.UUID) -> bool:
        """Verify the global currency configuration for the tenant"""
        return await self.md_client.check_pricing_readiness(company_id)
