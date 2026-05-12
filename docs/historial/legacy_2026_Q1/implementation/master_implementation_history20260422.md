# InternoCore: Implementation History - 2026-04-22

## Architectural Decision: Concept-Based Inventory Movements

### Context
To ensure a consistent Kardex and audit trail across the multi-tenant monolith, every inventory movement must be associated with a `MovementConcept`. Previously, these were optional and used localized Spanish names, leading to data fragmentation.

### Implementation
1. **Repository Layer**: The `MasterDataRepository` now handles "Lazy Initialization". If a company requests concepts and has none, the system JIT-seeds the 3 core English concepts (`PUR-REC`, `SAL-DIS`, `INT-TRA`).
2. **Inheritance**: Repositories now query using `OR (company_id = X, group_id = Y)`, allowing all companies in the "Interno Global Operations" group to share a standardized catalog.
3. **Command Handlers**: `TransferCommandHandler` was updated to require `concept_id` in `InitiateTransferCommand` and `CompleteTransferCommand`.
4. **Environment Readiness**: `common/config.py` was purged of `localhost` defaults to meet AWS Readiness criteria.

### Verification
- **Container Test**: `docker exec ... python inventory_service/scripts/flows/flow_5_ict_binational.py` confirmed cross-border transfers correctly record `INT-TRA` concepts for both MX and US companies.
- **Audit**: `generate_code_graph.py` reports **100% Compliance**.

---

## Phase 68: Frontend Concept-Guard Architecture (Signal-Safe Inventory Integration)

### Context
With the backend now mandating `concept_id` for all inventory movements, the Angular frontend needed a zero-null-propagation architecture to prevent 400/422 errors during catalog cold-start or tenant switches.

### Key Architectural Decisions

#### 1. Deterministic Concept Resolution (Signal-Safe)
`MasterDataService.resolveConceptByCode(code)` returns `null` if `catalogsLoaded()` is false. This prevents any component from resolving a concept during the LOADING window — avoiding race conditions on tenant context switches.

```typescript
resolveConceptByCode(code: string): Concept | null {
  if (!this.catalogsLoaded()) return null;  // Hard guard
  return this.concepts().find(c => c.code === code) ?? null;
}
```

#### 2. Three-State Catalog Guard (`ConceptCatalogState`)
```typescript
'LOADING' → catalog fetch in progress → block all submit buttons
'READY'   → concepts available → concept_id can be resolved
'ERROR'   → no concepts after load → show retry UI
```

#### 3. Component-Level Concept Guard Pattern
Each write component (Transfer, Inbound) declares reactive `computed()` signals:
```typescript
readonly transferConceptId = computed(() =>
  this.masterData.resolveConceptByCode('INT-TRA')?.id ?? null
);
readonly canSubmitTransfer = computed(() =>
  this.isFormValid() && this.transferConceptId() !== null
);
```

#### 4. Fallback UI (Defensive Block)
If concept is still null when submit is triggered (belt-and-suspenders), a toast shows "Configurando Empresa..." and the operation is aborted — never sending `concept_id: null` to the backend.

#### 5. Display Duality
- UI surfaces: `concept_name` (e.g. "Recepción de Compra")
- Internal logic: `concept_id` (UUID)
- Technical fallback: raw `type` string for legacy documents without concept

### Standard System Concept Codes
| Code     | Display Name (ES)          | Movement Type |
|----------|---------------------------|---------------|
| INT-TRA  | Traspaso Inter-Empresa    | TRANSFER      |
| PUR-REC  | Recepción de Compra       | ENTRY         |
| PUR-RET  | Devolución a Proveedor    | EXIT          |
| ADJ-POS  | Ajuste Positivo           | ENTRY         |
| ADJ-NEG  | Ajuste Negativo           | EXIT          |
| SCRAP    | Merma / Baja de Material  | EXIT          |

### Files Modified
- `frontend/src/app/core/models/domain.types.ts`
- `frontend/src/app/core/services/master-data.service.ts`
- `frontend/src/app/core/services/inventory.service.ts`
- `frontend/src/app/modules/inventory/inventory-transfer.component.ts`
- `frontend/src/app/modules/inventory/inventory-inbound.component.ts`
- `frontend/src/app/modules/inventory/inventory-documents.component.ts`
- `frontend/src/app/modules/inventory/inventory-dashboard.component.ts`
