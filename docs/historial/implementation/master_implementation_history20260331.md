# Master Implementation History - 2026-03-31

## Inventory Transfer & Anexo 24 Compliance

### Frontend Updates
- **Minimalist Industrial UI**: Refactored `inventory-transfer.component.ts` layout into huge tactile buttons to support warehouse operators wearing gloves and goggles. Standardized height (`140px`) across all selection cards and dropdowns to create an immaculate grid.
- **Inter-Company Workflow**: Configured the workflow to distinguish between Internal Transfers and External/Inter-company transfers. For external companies, the target warehouse is "Delegated to Receiver".
- **Anexo 24/30 UI Logic**: Incorporated detailed Customs Compliance block for binational operations:
  - Toggle between **Temporal (IMMEX)** and **Definitiva**.
  - Dynamic Custom Pedimento key formatting mapping: `IM` (Materia Prima), `AF` (Activo Fijo), `A1` (Importación Definitiva), `RT` (Retorno), `V1` (Virtuales/Venta), `EXPORT_ENTRY` (EEI).
  - Validation: Requires Folio EEI and Pedimento Key.
  - Item Ledger Visual Hint: Shows "Vinculado a Saldo de Pedimento" for traceability in binational mode.
- **Bugfixes**: Remedied complex Angular NG5002 template chunk syntax errors caused by unclosed `div` brackets within the industrial card `@if` wrappers.

### Backend Updates
- **API Router Mounting**: Fixed the 404 error during binational dispatch on `POST /api/v1/inventory/transfers/dispatch` by properly including the `inventory.py` router inside `main.py`.
- **Zero-Trust Transit Provisioning**: Implemented `ensure_transit_warehouse` in `SQLAlchemyInventoryRepository` to auto-provision virtual transit warehouses using deterministic UUIDv5. This ensures that stock is tracked as "In-Transit" (not in source, not in destination) until receipt is confirmed.
- **Persistence & Transaction Fix**: Resolved a critical issue where the inventory API returned "success" but didn't save any data due to missing `await session.commit()` in the `dispatch_transfer` and `receive_transfer` endpoints.
- **Auth Governance & Shift Management**: 
  - Standardized `RefreshToken` model to use `MultiTenantBase`, ensuring it includes required `tenant_id` and `group_id` columns (Governance Phase 41).
  - Fixed `NotNullViolationError` for `tenant_id` in `RefreshToken` by updating `SelectCompanyCommandHandler` and the refresh token endpoint.
  - Increased access token lifespan to 12 hours (720 minutes) to accommodate industrial shifts and minimize re-auth friction.

### Architectural Pivot & Phase 41 Start
- **Pivot: Multi-tenant Status Table**: After analyzing the legacy .NET source (`Interno.Inventory/Models/Catalog/MaterialStatus.cs`), we redirected the status management from hardcoded Enums to a dynamic `inventory_statuses` table. This allows each company to define their own state names (e.g., `En Tránsito` vs `In-Transit`) while the system maintains the underlying `CODE` (e.g., `IN_TRANSIT`) for logic.
- **Reversion**: Deleted the `0dbc27a674e2` Alembic Enum migration and reverted `DocumentStatus` in `app/models/document.py` to its original 3 states.
- **Status**: ✅ Plan Re-aligned & Task tracker updated.

### Next Steps & Business Logic (Feedback from Customs SME - Maritza)
- The architecture requires integrating **FIFO/PEPS traceability** to calculate "Descargos" against the oldest inbound `Pedimento`.
- We need to incorporate deeper identifier columns in our inventory models (either via `Items` or `Batches`):
  - **País de Origen** (Where it was manufactured, not dispatched).
  - **Fracción Arancelaria** (Tariff code for taxes).
  - **UMT (Unidad de Medida de Tarifa)** vs internal `uom_id`.
- The `StartBinationalTransfer` command in the WMS should trigger an `InventoryExported` domain event picked up by a new `Compliance/Anexo24` module to auto-deduct standard balances.
