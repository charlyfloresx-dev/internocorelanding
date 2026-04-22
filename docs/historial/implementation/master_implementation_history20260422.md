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
