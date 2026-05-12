# InternoCore: Consolidated Tasks - 2026-04-24

## Phase: Backend Resiliency & Error Handling Stabilization

### [DONE] Technical Tasks
- **Frontend Build Optimization**: Resolved `TS2393: Duplicate function implementation` and `TS7006: Parameter 'u' implicitly has an 'any' type` errors in `master-data.service.ts` and `inventory-put-away.component.ts`. The frontend build `esbuild` process now completes successfully without halting.
- **Middleware Hardening**: 
  - Patched `InternoCoreGlobalMiddleware` to handle exceptions without crashing (`AttributeError: 'UnauthorizedException' object has no attribute 'status_code'`).
  - Added strict priority enforcement for `GOD_MODE_ADMIN` to prevent token roles (`OPERATOR`) from overriding explicit testing headers (`X-Admin-Master-Key`).
- **Domain Exceptions**: Expanded `DomainException` and `UnauthorizedException` in `common/exceptions.py` to include class-level `status_code` defaults.
- **Database Idempotency**: Fixed `products` constraint violations (`NotNullViolationError` for `min_order_qty`) by applying `server_default=text('0')` to all numerical metrics (`min_order_qty`, `max_order_qty`, `safety_stock`).
- **Database Unified Seed**: Updated `unified_industrial_seed.py` with explicit keyword arguments for the new order quantity metrics ensuring zero ambiguity during monolith initializations.
- **Dynamic ID Testing**: Refactored `debug_inventory_post.py` to use dynamic SQL lookups (`resolve_ids()`) instead of hardcoded UUIDs, fully resolving `DataError: invalid UUID length` during integration testing.
- **E2E Flow Completion**: Validated all 6 multi-company inventory flows via CLI in the unified Postgres database, alongside the setup of transfer prices (MXN and USD).
- **HTTP POST Stabilization**: Verified `POST /api/v1/inventory/documents` is returning `200 OK` when properly integrated.
- **Frontend Intercompany Fixes**:
  - Refactored dropdown binding for `TRF-EXT` (requires external entity) to properly display "Empresa Destino" instead of "Cliente" in `inventory-document.component.ts`.
  - Fixed mathematical precision bugs during `printInvoice()` caused by parsing string-based decimals.
  - Added visual badge for `pending_financial_valuation` directly to the `inventory-documents.component.ts` UI table.
- **Master Data Seeding**: Verified `seed_concepts_and_warehouses` injects `TRF-EXT` with `MovementType.TRANSFER` and `requires_external_entity: True`.

### [PENDING] Backlog
- **God Mode Hardening**: Replace hardcoded `"GOD_MODE_ACTIVE"` checking in `SubscriptionGuard` and middleware with securely injected AWS Secrets.
- **Frontend Catalog E2E**: Fully link the `concept-catalog.component.ts` smart form preview with the stabilized backend to observe end-to-end signal propagation.
- **Role-based Approval UI**: Add specific approval screens or God-Mode role checks for `TRF-EXT` transfers.
