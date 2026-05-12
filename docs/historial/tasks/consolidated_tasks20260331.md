# Consolidated Operations Tasks - 2026-03-31

## Completed 🟢
- [x] Redesign transfer component for operators in dark/bright industrial environments (Goggles + Gloves) using high-contrast oversized cards.
- [x] Integrate Anexo 24 compliance UI logic for Cross-Border transfers:
  - Toggle between IMMEX Temporal vs Definitiva regime.
  - Dynamically disable/enable specific keys (`IM`, `AF`, `A1`, `RT`, `V1`, `EXPORT})$.
  - Provide operator hints indicating item linkages with Customs Balances.
- [x] Resolve `NG5002` syntax exceptions triggered by orphaned tags during template refactoring.
- [x] Align exact dimensions and constraints of the selector buttons to `h-[140px]`.
- [x] Fix `404` error for the dispatcher backend request by registering the missing `inventory.py` router inside `main.py`.
- [x] Implement deterministic transit warehouse auto-provisioning (UUIDv5) for Zero-Trust ownership compliance.
- [x] Fix critical `500` error (ERR_WAREHOUSE_ACCESS_DENIED) by correctly associating transit warehouses with the destination company.
- [x] Fix critical persistence bug (missing `commit()`) in inventory transfer endpoints.
- [x] Standardize `RefreshToken` for Multi-Tenancy governance (Phase 41) and fix `tenant_id` visibility issues.
- [x] Extend JWT Token lifespan to 720 minutes (12 hours) for industrial shifts.
- [x] **Redirected**: Revert hardcoded Enums in favor of a Multi-tenant `InventoryStatus` table (Legacy alignment).

## Backlogged 🔴 / Next Steps
### Subdomain: Compliance / Anexo 24/30 Integrations
- [ ] Implement `CustomsDocument` value object structure to validate the 21-digit Folio/Pedimento format (2 year digits + 2 aduana + 4 patente + 1 last digit of year + 6 running).
- [ ] Expand the Inventory Items/Batches SQL Models to support required compliance columns: `País de Origen`, `Fracción Arancelaria`, and `UMT (Unidad de Medida de Tarifa)`.
- [ ] Connect the `StartBinationalTransfer` command to raise an `InventoryExported` domain event.
- [ ] Architecture a generic Event Listener logic in a new `Compliance Module` to handle FIFO/PEPS descargo algorithm.
- [ ] Enforce conditional behavior: Require an active IMMEX scheme flag linked to the Origin `CompanyId` before accepting Temporal Pedimentos.

### Subdomain: Inventory API
- [x] Actually process the frontend payload inside `@router.post("/transfers/dispatch")` matching the UI properties `<quantity`, `uom_id`, `customs_pedimento`, `customs_regime`, `customs_pedimento_key>`.
- [ ] Implement `InventoryReceived` event to finalize the `In-Transit` balance deduction.
- [ ] Provide comprehensive tests evaluating the cross-border boundaries of inter-company transfers vs identical company transfers.
