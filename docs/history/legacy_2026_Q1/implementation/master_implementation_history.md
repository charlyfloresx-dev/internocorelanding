# Master Implementation History â€” 2026-03-24

## Session Summary: Frontend Localization & i18n Handshake

This session was dedicated to the comprehensive internationalization (i18n) of the Interno Core frontend. The objective was to replace all hardcoded Spanish strings with a dynamic, key-based translation system (TranslatePipe / TranslationService) and standardize system messages.

### Technical Decisions & Architectural Patterns

1.  **Reactive i18n Engine**:
    *   **Pattern**: Signal-based `TranslationService` integrated with a `pure: false` `TranslatePipe`.
    *   **Decision**: Opted for a "Fallback Included" translation pattern: `{{ 'key' | translate:'Fallback Text' }}`. This ensures the UI remains functional (in Spanish/English) even if the translation key is missing from the JSON during development.
    *   **Instant Update**: By marking the `TranslatePipe` as `pure: false`, we ensured that the UI re-renders immediately as soon as the active language signal changes in the `TranslationService`.

2.  **Schema Homologation (en.json / es.json)**:
    *   **Decision**: Centralized all common UI labels (Cancel, Save, Success) under a `common` namespace to reduce redundancy.
    *   **Module Isolation**: Created dedicated namespaces for `auth`, `inventory`, `catalog`, and `settings.users` to keep translation files maintainable as the project grows.

3.  **UI Resilience & Bug Fixes**:
    *   **Inventory Dashboard**: Fixed a critical compilation blocker (NG5002) in `inventory-dashboard.component.ts`. A duplicated `<input>` tag was interfering with the template parser.
    *   **User Management**: Localized complex dynamic messages in `UserManagementComponent`, including permission matrices and toast notifications.

### Implementation Milestones

-   âœ… **Main Layout**: Localized side-nav, header, and multi-tenant context labels.
-   âœ… **Auth Module**: Migrated the entire login flow (credentials, QR/RFID scanner, forgot password) to the i18n system.
-   âœ… **Inventory Dashboard**: Full translation of metrics, alerts, and movement ledger headers.
-   âœ… **Product Catalog**: Localized the master product list and action buttons.
-   âœ… **User Management**: Migrated the administration of roles and permissions to the translation engine.

### Blockers & Resolutions

| Blocker | Resolution |
| :--- | :--- |
| `NG5002` Template error in Inventory Dashboard | Manually audited the template and removed a rogue `<input>` tag that was breaking the esbuild process. |
| Hardcoded procedural strings in TS files | Injected `TranslationService` in the component classes to resolve keys dynamically before sending them to the `ToastService`. |
| Missing persistence in language selection | The current `TranslationService` defaults to 'es', but the infrastructure is ready to load preferences from local storage in the next phase. |

### Next Steps

1.  **Remaining Modules**: Audit and localize `Production`, `Quality`, and `WMS` modules.
2.  **Form Validation**: Translate Angular Reactive Form validation messages (e.g., "Field required").
3.  **Backend Message Sync**: Continue the synchronization of backend error codes with frontend translation keys.

---

## Session Summary: Legacy Feature Adoption & Industrial Hardening

This session focused on migrating critical architectural patterns from the legacy `frontend` engineering logs into the new "Interno Core" Angular 21 frontend to achieve industrial-grade resilience and security.

### Technical Decisions & Architectural Patterns

1. **Zero-Trust Identity Handshake ðŸ›¡ï¸**
   - Refactored `AuthService.restoreSession()` from a synchronous `localStorage` read to an active, asynchronous validation against a new `GET /api/v1/auth/me` endpoint in the Python `auth_service`.
   - Bootstrapped this active validation into the Angular `APP_INITIALIZER`, completely blocking application startup until the backend validates the volatile `selection_token` and persistent `access_token` session. This eliminates "zombie sessions" and enforces the 3-phase handshake strictly.

2. **Industrial Resilience (Offline-First) ðŸ­**
   - Implemented a "Cache-Then-Fallback" pattern across core services (`MasterDataService` and `InventoryService`). 
   - Requests that succeed cache their payload in `localStorage` under the `ic_cache_` namespace. If subsequent network requests fail (e.g., due to common industrial WiFi degradation), the services catch the error and return the cached data, accompanied by a warning.
   - Integrated `SystemHealthService` reporting into these requests to actively track and report the `isReadOnly` state.

3. **UI Governance & Readiness Gatekeeper ðŸ“¦**
   - Addressed the "Empty Dashboard Syndrome". Implemented an active `isReady` signal and `checkReadiness()` flow within the `InventoryDashboardComponent` to force users through setup if master data (UOMs, Categories, Brands, Warehouses) is missing.
   - Refined type casting in `inventory.service.ts` for strictly typed data models (`UOMRead`, `CategoryRead`, `BrandRead`) returned from the cache interceptor.

4. **Transaction Integrity ðŸ“**
   - Implemented Idempotency Key Injection. The `multi-tenant.interceptor.ts` now identifies mutation requests (`POST`, `PUT`, `PATCH`, `DELETE`) and automatically injects a `X-Client-Request-ID` (UUID v4) header derived from the `X-Correlation-ID`. This ensures API requests can be safely retired without creating duplicate ledger entries.
   - Enhanced the `AuditFooterComponent` to support a "Triple Identity" view, exposing the Folio as the readable title, presenting the UUID as a copyable technical ID via a tool-tipped element, and including standard User / Date metadata.

### Blockers & Resolutions
- Addressed several `esbuild` typing strictness errors when assigning `[]` to statically typed Arrays. Fixed by casting values as `unknown` then back to their specific `*Read` types in the catalog mapping.
- Handled interceptor interference gracefully by making `isAuthRoute` and `isAuxiliaryService` explicit to prevent security loops on `/health` checks.

### Next Steps
- Implement remaining Idempotency checks on endpoints via the backend decorators.
- Proceed to harden cross-service orchestration and solidify E2E tests, ensuring that the legacy behaviors adopted today seamlessly integrate with future inventory and WMS logic.

# 29 de Marzo, 2026 - Viatra Core (Fintech & Sentinel)

- Implementation of Booking Engine, Stripe integration, and Sentinel Bots.
- Status: v0.8.5 Cluster Hardened.

---

# 14 de Abril, 2026 - Hub Stabilization (Pricing & B2B Immortality)

## Session Summary: Industrial Pricing Engine & B2B Integrity

This session finalized the stabilization of the Interno Core pricing ecosystem, focusing on achieving 100% data integrity for B2B contracts and resolving critical runtime validation errors.

### Technical Decisions & Architectural Patterns

1. **Immutable B2B Contract Architecture**:
   - **Pattern**: "Soft-Close & Insert" for `PriceAgreement` records.
   - **Decision**: To maintain absolute forensic auditability, logical updates of existing prices were prohibited. Every change generates a new version while the previous one is marked with `valid_until`.

2. **API Mapping Over Schema Complexity**:
   - **Problem**: Pydantic validation conflicted with SQLAlchemy's `Money` composite objects due to private field shadowing (`_amount`).
   - **Decision**: Implemented an explicit mapper (`map_price`) in the endpoint layer instead of complex Pydantic customization. This keeps the persistence layer decoupled from the API contract and resolved all 500 errors.

3. **Hybrid Pricing UI**:
   - **Decision**: Refactored the `ProductPriceListComponent` into a tabbed interface. This allows separation of Master Prices (List-based) from tailored B2B Agreements (Partner-based) while maintaining a clean, industrial UX.
   - **Tooltip Governance**: Implemented a non-intrusive but high-visibility yellow tooltip for "Missing Data" alerts, improving the "Go-Live" readiness awareness for catalog items.

### Implementation Milestones
- [x] **Relational Resilience**: Resolved 404 path mismatches between `/prices` and `/products` across the frontend/backend bridge.
- [x] **DI Optimization**: Fixed a circular dependency/missing instantiation in the `CurrencyService` repository layer.
- [x] **Industrial Testing**: Integrated a full `pytest` suite for pricing validation inside the `master-data-service` container.

### Blockers & Resolutions
- **500 Internal Error (Pydantic)**: Resolved by manual field mapping from `Money` objects to `ProductPriceRead` schema.
- **SQLite UUID Compilations**: Patched `conftest.py` with a custom `TypeDecorator` to support in-memory testing of Postgres-based models.
- **Frontend 404s**: Corrected `MasterDataService` endpoint paths to match the backend router prefixes.

