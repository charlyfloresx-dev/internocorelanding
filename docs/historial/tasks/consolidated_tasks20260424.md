# Consolidated Tasks - 2026-04-24
## Phase 69: Industrial Zero-Hardcode Frontend (SSOT Enforcement)

### 1. Backend Synchronization
- [x] Audited Code Graph for compliance: **100% CLEAN**.
- [x] Verified Master Data Client for cross-service lookups.

### 2. Frontend De-Mocking
- [x] Removed `getMockWarehouses` and `getMockConcepts` from `InventoryService`.
- [x] Purged `MAT-001`/`MAT-002` fallback data from `ItemSearchComponent`.
- [x] Replaced hardcoded UUIDs in `InventoryDocumentComponent`, `InventoryPutAwayComponent`, and `ItemSearchComponent`.
- [x] Implemented `resolveUomByCode` and `resolveConceptByCode` in `MasterDataService`.

### 3. UI Industrialization
- [x] Converted `docks` in `InventoryInboundComponent` to dynamic computed signal from warehouses.
- [x] Updated "Smart Form Preview" in `ConceptCatalogComponent` to use real tenant warehouses.
- [x] Fixed template iterations for signal-based collections.

### 4. Technical Debt Resolved
- [x] Eliminated diagnostic `console.log` from inventory filtering logic.
- [x] Hardened `is_active` concept filtering to handle optional/null states safely.

### Pendientes (Backlog):
- [ ] E2E Validation of "TRANSFER" flow with dynamic concept resolution.
- [ ] Audit Remaining Handhelds (Shipping, Cycle Count) for any hidden mock artifacts.
- [ ] Finalize UOM conversion logic for non-piece units (FT, KG).
