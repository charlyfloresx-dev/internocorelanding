### [2026-04-17] Phase 55: CloudFront Deployment & API Sync
- **Angular Build Stability**: Corregido `angular.json` para habilitar `fileReplacements` (missing in prod config).
- **Environment Sync**: Actualizado `environment.prod.ts` para apuntar al ALB de AWS en Ohio.
- **S3 Sync Protocol**: Ajustado despliegue de S3 para servir desde la raíz, eliminando la colisión del subdirectorio `/browser/`.
- **CloudFront Invalidation**: Automatizada la invalidación de caché tras el despliegue de assets.
- **Status**: ✅ DEPLOYED ON CLOUDFRONT

### [2026-04-16] Phase 44: Media Assets Support & URL Normalization
- **Image Interceptor**: Implemented a global `imageInterceptor` to handle multi-tenant asset normalization. Automatically prepends `environment.assetsUrl` to relative paths (`photo_path`, `profile_url`) in API responses.
- **SecureImage Pipe**: Created a standalone `secureImage` Pipe to simplify template rendering. Supports default placeholders and handles mixed relative/absolute URLs gracefully.
- **Environment Config**: Introduced `assetsUrl` token for centralized control of the media domain (e.g., `momentos.com` for local dev parity).
- **Architecture**: Registered the new interceptor in `app.config.ts`, ensuring all existing and future modules benefit from unified asset resolution.

### [2026-04-15] Phase 49.8: Outbound Shipping & Compliance (Embarques Industrial)
- **Shipping Handheld Module**: Developed `InventoryShippingComponent` (`/inventory/shipping`) with Folio-driven validation and industrial high-contrast ergonomics.
- **Operator Badge Validation**: Integrated a mandatory driver badge scan as a prerequisite for dispatch, establishing the link to upcoming cross-border identity modules in `hr_service`.
- **UI Responsiveness**: Expanded handheld layouts to `max-w-4xl` and `max-w-7xl` to better utilize industrial tablet real estate (iPad Pro).
- **Manual Mode Toggle**: Added a clear "Manual vs Folio" state toggle in the standard reception screen to improve warehouse floor decision-making.

### [2026-04-15] Phase 48: Industrial Integrity & "The Density Guard"
- **Registry Cache**: Implemented `InventoryRegistryService` for $O(1)$ in-memory SKU lookups, enabling zero-latency scanning for 10k+ products.
- **The Density Guard**: Added real-time location capacity validation in the Put-Away flow, including a semantic visual bar (Green/Amber/Red) and industrial audio alerts (110Hz Overflow Beep).
- **Manual Entry Mode**: Integrated high-speed manual SKU input with auto-hydration from the registry cache and pre-emptive capacity checks.
- **Scan Hygiene**: Ported `getNumber` regex logic to sanitize barcode scans in real-time.

### [2026-04-15] Phase 47: Industrial Put-Away & Session Stability
- **Put-Away Module**: Developed high-priority handheld interface for DOCK-to-RACK relocation with 3-step scan flow and F2 confirmation.
- **Audio Feedback**: Integrated `playIndustrialBeep` (200Hz/880Hz) for real-time haptic/audio validation on the warehouse floor.
- **Session Resilience**: Patched `StockLevelComponent` with a resilient parsing engine to handle variant microservice response structures without UI death.
- **Identity Fix**: Resolved session loss on refresh by implementing defensive attribute access for user profiles.

### [2026-04-15] Phase 46: Industrial Scalability & Warehouse Stabilization (Anexo 24)
- **Scalability (10k+ SKUs)**: Implemented server-side pagination and search in `StockLevelComponent` and `InventoryService`.
- **UI Architecture**: Updated global `ApiResponse` to include `total_count` and pagination metadata, standardizing industrial report handling.
- **Bug Squashing**:
    - Resolved `TS2341` and `NG5002` compilation errors in Inventory modules.
    - Fixed API integration in `StockLevelComponent` by standardizing service layer usage and correcting JSON parsing.
- **Visual Compliance**: Implemented risk-aware UI with industrial aesthetics for Anexo 24 auditing, including aging alerts and stock status filters.

### [2026-04-14] Phase 45.1: Pricing Stabilization & B2B Immortality (Final)
- **Hybrid Tabbed UI**: Refactored `ProductPriceListComponent` to support a clean separation between Master Prices and Partner-specific Agreements.
- **B2B Lifecycle**: Fully integrated the "Soft-Close & Insert" pattern for price agreements, ensuring frontend parity with the backend's immutable architecture.
- **Quality Tooltips**: Implemented modern, yellow-themed active tooltips for "Missing Data" alerts (SAT codes, UOM) in the catalog dashboard, improving operational governance.
- **Path Resolution**: Corrected API paths in `MasterDataService` to properly bridge the `/api/v1/prices` backend module.

### [2026-04-14] Phase 45: Industrial Pricing & Identity Stabilization (Frontend UX & RBAC)

### [2026-04-13] Session 7: Control Tower B2B - Mass Price Import
- **Industrial Dashboard**: Created `PriceImportDashboardComponent` (Standalone) with Neon Cyan aesthetics. Handles general price lists and partner-specific agreements.
- **UX Features**: 
    - Full Drag & Drop support for CSV with active drag state transitions.
    - Integrated result matrix with side-by-side display of "Immutable Creations" vs "Failed Integrities".
    - Forensic error reporting per CSV line.
- **Service Layer**: 
    - Extended `MasterDataService` to support dynamic template downloads (general vs partner-based).
    - Implemented `importPrices` with `FormData` and native error interception.
- **Dialog Orchestration**: Catalog header integration using `MatDialog` with automatic catalog `loadProducts()` refresh on modal close.
- **Styles**: Defined `ic-dark-dialog` and glassmorphism overlays in global CSS.

### [2026-04-10 EOD] Session 6: RBAC Governance + Excel Grid Wizard


Guard-First UI: all catalog modals disable form/delete for non-admin via AuthService.
Excel Wizard: ProductWizardComponent full-screen grid, Tab/Enter nav, price optional.
Incomplete Panel: computed signal flags products missing price/SAT/category.

Files: partner-modal, concept-modal, uom-modal, master-data.service, product-wizard.component (NEW), product-catalog.component
Status: BUILD CLEAN 17:41:55

---

### [2026-03-30] â€” Session 6: Inventory Context Virtualization & Routing Match
- **Decision**: Elevate Physical Warehouse Selection to a Global Module Context and resolve 404/422 discrepancies in cross-border transfers.
- **Reason**: The transfer routing payload lacked strict alignment with FastAPI boundaries (`/api/v1/inventory/transfers/inter-company`) and required mandatory Pydantic structural components (like `uom_id`). From a UX perspective, physical operators do not select "origin" per transaction; they operate from a fixed terminal logic.
- **Impact**:
-   **Architecture Pivot (Pending Modal)**: Mapped out the requirement for a mandatory Warehouse Selection Modal upon entering the Inventory Module. This will act as the genesis for location-aware RBAC.
-   **Cascade Reliability**: Deprecated the flat origin card in favor of a global header dropdown `originWarehouseId` that automatically back-computes the parent `company_id` for zero-trust routing.
-   **Compliance Fallback**: Injected a proxy `uom_id` and geographical proxy `company_id` into the payload and UI computed functions to allow full utilization of the sparse backend Docker seed data.
- **Status**: âœ… COMPLETED

### [2026-03-30] â€” Session 5: Dashboard High-Fidelity & Industrial Resilience
- **Decision**: Refactor `InventoryService` for fault-tolerant catalog loading and harmonize "Mission Control" UI for high-contrast/tablets (iPad Pro).
- **Reason**: 500 errors in secondary catalogs (Categories/Brands) were crashing the entire dashboard due to strict `Promise.all` logic. The header selector had z-index occlusion and poor contrast on high-resolution displays.
- **Impact**:
-   **Header Minimalism**: Transitioned to a borderless, transparent context selector with `z-20` elevation and `group/tenant` click-protection.
-   **Technical Resilience**: Implemented `Promise.allSettled()` in `loadCatalogs` and `X-Silent-Error` header handling to suppress non-fatal dashboard alerts.
-   **Iconography & UX**: Standardized `IN/OUT` and `ENTRADA/SALIDA` movement mappings. Added a premium "Back to Dashboard" exit path in the document confirmation flow.
-   **Visual Symmetry**: Calibrated "Mission Control" title scaling (5xl desktop / 3xl mobile) to improve layout balance.
- **Status**: âœ… COMPLETED

### [2026-03-24] â€” Session 4: Full Frontend Internationalization (i18n) & Localization
- **Decision**: Replace all hardcoded Spanish strings and labels with a dynamic, key-based translation system (`TranslatePipe` and `TranslationService`).
- **Reason**: Enable multi-language support (ES/EN) across all core modules to prepare for international deployment and standardize system messages.
- **Impact**:
-   **Infrastructure**: Implemented a reactive, Signal-based i18n engine with fallback support.
-   **Module Localization**: Completed the migration for `Login`, `Inventory Dashboard`, `Product Catalog`, `User Management`, and `Main Layout`.
-   **Bug Fix**: Resolved a critical template compilation error (`NG5002`) in the `InventoryDashboardComponent`.
-   **Standardization**: Populated `en.json` and `es.json` with comprehensive keys for both UI labels and procedural toast notifications.
- **Status**: âœ… COMPLETED

### [2026-03-24] â€” Session 3: Tenant Selector Homologation & Catalog Restoration
- **Decision**: Refactor `MainLayoutComponent`'s tenant selector to match the `Dashboard`'s high-fidelity UI and logic, and restore the "Nuevo Producto" action in the catalog.
- **Reason**: Discrepancy between header and dashboard selectors caused user confusion, and the missing "Create" button in the catalog was a major functional blocker.
- **Impact**:
-   **Header Identity**: Unified `activeCompanyName()` resolution using strictly current shared signals.
-   **Catalog Action**: Added "Nuevo Producto" button with context-aware validation (requires active tenant).
-   **Persistence**: Implemented `localStorage` pack for company list to bridge the state between refresh cycles.
-   **Status**: âœ… COMPLETED

### [2026-03-23] â€” Session 2: UX Resilience & Rate Parsing Robustness
- **Decision**: Refactor `MainLayoutComponent` moving the `CompanySelector` to the header and enforce `scopes` strict mapping inside `AuthService` logic.
- **Reason**: Fix silent failures where the sidebar menu wouldn't render the `Inventarios` tab for users despite possessing valid scopes, and allow a true global "hot-switching" pattern for the user without needing to open the sidebar.
- **Impact**:
  - `CompanySelector` is fully operational globally with instant signal propagation across all services.
  - `NavigationService` correctly isolates tabs defaulting securely to the dashboard instead of rendering a blank view if permissions are delayed.
  - Reduced component friction in standard workflows.
- **Status**: âœ… COMPLETED

### [2026-03-23] â€” Phase 35: Compliance Binacional & Smoke Testing
- **Decision**: Enforce customs documentation only when Country IDs differ in transfers.
- **Reason**: Legal compliance in cross-border operations (e.g. MX-USA) requires traceable customs references (Pedimento). Handled via BusinessRuleException in the handler and conditional form fields in Angular.
- **Impact**:
  - InventoryTransferComponent displays customs_pedimento input only for international routes.
  - InventoryDocumentsComponent shows legal cues (gavel icon) for verified binational transfers.
  - Multi-company transfers now block without pedimento if country codes mismatch.
- **Status**: âœ… COMPLETED

# Engineering Log - Interno Core MES

### [2026-04-10] — Session 5: Partner Creation Integration & UI Stability
- **Decision**: Integrate a unified `PartnerModalComponent` across all transactional modules and implement `@if` based visibility.
- **Reason**: Reduce code duplication and fix "phantom overlays" caused by `[hidden]` logic. Ensure partners can be created on-the-fly during inventory movements without losing context.
- **Impact**:
  - **Shared Component**: Created `PartnerModalComponent` (Standalone) with simplified validation (RFC/Email optional).
  - **Visibility**: Implemented `@if (isAddingPartner())` pattern, ensuring DOM isolation for modals.
  - **Enum Synchronization**: Synchronized `PartnerType` enum between Angular services and FastAPI models.
  - **UX Polish**: Added close (X) buttons to all critical modals and improved saving-state recovery on errors.
- **Status**: ✅ COMPLETED


## Architecture Decisions

### [2026-03-23] Ã¢â‚¬â€� Phase 34: ICT Lifecycle Actions & WAC Precision
- **Decision**: Implement manual "Receive" and "Reclaim" actions in `InventoryDocumentsComponent`.
- **Reason**: Close the operational loop. Receivers need to verify quantities physically before the ledger reflects the final IN. Senders need a way to recover stock if the receiver rejects or abandons the transfer (Reclaim).
- **Impact**: 
  - Added "Confirm Receipt" and "Reclaim Stock" buttons with contextual behavior.
  - Implemented `receiveTransfer()` and `revertTransfer()` in `InventoryService` connected to the backend.
  - Added specific icons (`outbox`, `move_to_inbox`) and border-tag colors (Indigo/Cyan) to the movement ledger.
- **WAC Validation**: Successfully verified mathematical recalculation of WAC in the UI after receiving 100u ($20.00 final WAC for MAT-001).
- **Status**: Ã¢Å“â€¦ COMPLETED

### 1. Zoneless Angular 19
- **Decision:** Use `provideExperimentalZonelessChangeDetection()`.
- **Reason:** Maximize performance for industrial tablets and reduce bundle size.
- **Impact:** All change detection must be triggered via Signals or manual `markForCheck`.

### 2. Multi-tenant Handshake (T1/T2)
- **Decision:** Two-step authentication flow.
- **Phase 1 (Login):** Credentials -> `selection_token` + Company List.
- **Phase 2 (Selection):** `selection_token` + `company_id` -> `access_token` (JWT).
- **Reason:** Securely handle users with access to multiple plants/companies.

### 3. Identity Triple
- **Decision:** Every document must expose UUID, Sequence, and Folio.
- **Reason:** Compliance with audit trails (Sequence) and user-friendly search (Folio).

### 4. Immutable Ledger
- **Decision:** Documents in `CONFIRMED` state are `readonly`.
- **Reason:** Maintain data integrity in the inventory ledger.

### 5. Inter-Company Transfer Flow (WMS -> Inventory)
- **Origination:** Originated in WMS as `TRANSFER` type via `POST /transfers/inter-company`.
- **Validation:** `wms_service` validates that both source and target companies belong to the same `group_id` (Holding).
- **Kardex Dispatch:** 
    - `OUT` movement (`TRANSFER_DISPATCH`) from source warehouse.
    - `IN` movement (`TRANSFER_IN_TRANSIT`) to a Virtual Transit Warehouse (UUID5 hash based on target warehouse).
- **Monitoring:** `TransitAgeWorker` monitors transit time.
    - > 24 hrs: `WARNING`.
    - > 48 hrs: Critical `P3 Ticket` in `tickets_service`.
- **Reception:**
    - `OUT` movement (`TRANSFER_RECEIVE_TRANSIT`) from virtual transit warehouse.
    - `IN` movement (`TRANSFER_RECEIVE`) to destination real warehouse.

### 6. Audit & Visualization Points
- **Real-Time Dashboard:** `GET /dashboard/stock` shows `available` vs `in_transit_quantity`.
- **Immutable Ledger:** `movements` (Inventory) and `documents` (WMS) tables. Auto-signed via `BaseRepository` with `created_by`, `company_id`, and `transaction_id`.
- **Operational Logs:** Worker alerts logged to application console (Docker) and aggregated in CloudWatch/Kibana.
- **Inventory Service Sync**: Updated to support Postgres real data and Money VO composites.


 # #   2 0 2 6 - 0 3 - 3 0 :   I n v e n t o r y   C o n t e x t   R e f i n e m e n t   &   S t a b i l i t y 
 # # #   <Ø×ßþ  I n v e n t o r y T r a n s f e r C o m p o n e n t 
 -   F i x e d   s e l e c t i o n   f i l t e r i n g :   O r i g i n   l i s t   n o w   s c o p e s   o n l y   t o   t h e   c u r r e n t   ' X - C o m p a n y - I D ' . 
 -   G r o u p e d   d e s t i n a t i o n   s e l e c t o r :   C l e a r l y   s e p a r a t e s   I n t e r n a l   v s   E x t e r n a l   e n t i t i e s . 
 -   ' D e f i n i d o   p o r   R e c e p t o r '   l o g i c :   A u t o m a t e d   f o r   i n t e r - c o m p a n y   m o v e m e n t s . 
 -   T h e m e   i s o l a t i o n :   R e p l a c e d   h a r d c o d e d   s t y l e s   w i t h   s u r f a c e - a w a r e   T a i l w i n d   t o k e n s . 
 
 # # #   =ØÝ  D a s h b o a r d S e r v i c e 
 -   F i x e d   i n f i n i t e   c a l l   l o o p   f o r   m o v e m e n t s   f e e d . 
 -   A d d e d   c i r c u i t   b r e a k e r   f o r   o f f l i n e   m o d e   ( s w i t c h e s   a u t o m a t i c a l l y   t o   s y n t h e t i c   d a t a ) . 
 -   I n t e g r a t e d   ' X - C o m p a n y - I D '   h e a d e r   i n t o   t e l e m e t r y   p o l l i n g .  
 
