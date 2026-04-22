# InternoCore: Consolidated Tasks - 2026-04-22

## Phase: Master Data Industrialization & Flow Synchronization

### [DONE] Technical Tasks
- **Master Data JIT Seeding**: Implemented Lazy Initialization in `SQLAlchemyMasterDataRepository` to automatically create standard Movement Concepts and UOMs for new companies.
- **English Standardization**: Renamed all core catalog items to English standard names (`Pieces`, `PUR-REC`, `SAL-DIS`, `INT-TRA`).
- **Inventory Flow Sync**: Updated all 6 inventory scripts in `inventory_service/scripts/flows/` to resolve and inject mandatory `concept_id` values.
- **Docker Validation**: Successfully executed the Unified Seed and all 6 Inventory Flows inside the `interno-monolith` container, ensuring 100% environment parity.
- **Code Graph Audit**: Resolved `AWS_READINESS_VIOLATION` in `common/config.py` by removing hardcoded `localhost` references.

### [DONE] Frontend Inventory Industrialization (Phase 68 — Signal-Safe Concept Architecture)
- **`domain.types.ts`**: Added `code` to `Concept`, `ConceptCatalogState` type, `concept_id`/`concept_name` to `RecentActivityRow` and `InventoryDocument`.
- **`MasterDataService`**: Added `catalogsLoaded` (computed signal), `conceptCatalogState` ('LOADING'|'READY'|'ERROR'), `resolveConceptByCode(code)`, `resolveConceptsByType(type)`, `conceptsForType(type)`.
- **`InventoryService`**: Exposed `catalogsLoaded`, `conceptCatalogState`, `resolveConceptByCode` as delegates. Typed payloads for `initiateInterCompanyTransfer` and `dispatchInternalTransfer` now require `concept_id: string`.
- **`inventory-transfer.component.ts`**: `transferConceptId` / `internalTransferConceptId` reactive computeds. `canSubmitTransfer` blocks if catalog in LOADING state. Both ICT and internal transfer payloads inject `concept_id`.
- **`inventory-inbound.component.ts`**: `transferConceptId` (INT-TRA) and `purchaseConceptId` (PUR-REC) guards. `confirmReceipt` and `confirmBlindReceipt` block with "Configurando Empresa..." toast if concept is null.
- **`inventory-documents.component.ts`**: Type column shows `concept_name` (e.g. "Recepción de Compra") as primary label with technical type as subtitle. `getTypeIcon/Class` updated with concept-aware Spanish matching.
- **`inventory-dashboard.component.ts`**: Recent ledger maps `concept_name`/`concept_id` from API. StatusBadge shows business label. `filteredLedger` searches by concept name.

### [PENDING] Backlog
- **Unit Testing**: Add explicit test cases for the Lazy Initialization edge cases (e.g., group inheritance failure).
- **Deployment**: Final sync of ECS task definitions with the latest environment variables.
- **Backend Join**: Populate `concept_name` in `get_dashboard_telemetry` and `list_movements` via SQL JOIN with `inventory_movement_concepts`.
