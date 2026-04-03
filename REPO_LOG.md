# Interno Core - Global Engineering Log

Tracking the major milestones, architectural shifts, and technical decisions of the ecosystem.

## [2026-04-03] - Phase 42: Inventory Schema Synchronization & Traceability Hardening
- **Microservice Schema Isolation**: Addressed the conflict where `inventory_db` had ghost Foreign Key constraints pointing to a non-existent or empty `companies` table. Generated migration `13f1006bf066` to include the `companies` table correctly and updated `seed.py` to populate it as a local cache.
- **Traceability by Default**: Updated internal inventory flows (`flow_1_entry.py`, `flow_2_exit.py`) to create `InventoryDocument` records automatically, ensuring manual warehouse operations are visible in the frontend dashboard.
- **Backend Robustness**: Resolved `UnboundLocalError` in `TransferCommandHandler` and improved script idempotency to match the global `master_seed.py` orchestration.
- **Status**: ✅ COMPLETED (Inventory Kardex & Dashboard Synced)



## [2026-04-01] - Phase 41: Binational UI Stabilization & Infrastructure Persistence
- **Defensive Schema Initialization**: Resolved critical startup collisions between `inventory_service` and `master_data_service` schemas. Implemented `Base.metadata.create_all()` preemptively in `inventory_service` and inserted `_table_exists()` cross-domain safety checks into Alembic. PostgreSQL containers can now boot, auto-generate schemas idempotently, and completely survive `docker compose down -v` scenarios.
- **Frontend Signals Resilience**: Addressed Angular template compilation breaking due to lost computed signals (`filteredOriginCompanies` and `filteredDestWarehouses`). Reattached the "Ghost Stock" logic gracefully to the UI, enabling seamless multi-tenant dropdown rendering in the Logistics dashboard.
- **Test Matrix Hardening**: Stabilized `test_full_ict_cycle.py` tests natively in the Docker context, fully authenticating inter-company flows matching the new architectural constraints.
- **Status**: ✅ COMPLETED (Binational Flow Ready for Finance Module)


## [2026-04-01] - Phase 40: Binational Audit & Compliance Agent
- **Compliance-First Operations**: Successfully transitioned the inter-company transfer system to an "Audit-Ready" architecture. Implemented the `TransferAuditService` (Pre-Flight Agent) to intercept and validate tax & customs compliance (Anexo 24) on binational routes.
- **Fiscal Watermarking**: Engineered the "Administrative Debt" pattern for pricing. The system now allows physical stock movement even without a final transfer price, automatically flagging documents as `pending_financial_valuation` for later regularization by Finance rather than blocking the truck.
- **Binational FX & Mirroring**: Integrated mandatory `exchange_rate_dof` reporting for MX $\rightarrow$ US transfers. The backend now accurately generates USD-valued "Draft" inbound documents for mirror entities, ensuring real-time valuation parity.
- **Customs Ledger Logic**: Integrated FIFO-based pedimento tracking and aging alerts within the audit flow. Users must now explicitly acknowledge risks for material with expiring legal stay (< 15 days).
- **Status**: ✅ COMPLETED (Binational Audit Agent Live)

---

## [2026-03-31] - Phase 41.1: Inventory Service Restoration & Schema Alignment
- **Critical Fix (Startup Crash)**: Identified and resolved a fatal `ImportError` in `app/api/v1/endpoints/inventory.py` and `app/services/inventory.py` where a stale service name (`InventoryService`) was being referenced instead of the correct `InventoryTransactionService`. This crash was the root cause of the silent service failure and subsequent `404 Not Found` errors.
- **Schema Resilience**: Updated `TransferDispatchCmd` and `TransferReceiveCmd` in `app/schemas/stock.py` to make `weight` and `transfer_id` optional. This aligns the backend with the "lean" payloads sent by the Angular frontend, preventing P2P (Point-to-Point) validation failures.
- **Security Normalization**: Transitioned the inventory dispatch endpoints from manual header-based `X-Company-ID` extraction to the robust, JWT-centric `SubscriptionGuard`. This enforces Zero-Trust multi-tenancy by deriving the target company directly from the cryptographically signed token.
- **Verification**: Executed a clean, no-cache Docker rebuild and verified service health via local `curl` telemetry. The endpoint is now actively listening and processing requests.
- **Status**: ✅ COMPLETED (Hotfix Applied)

---

## [2026-03-31] - Phase 41.2: Transit Warehouse Provisioning & Auth Governance
- **Transit Warehouse (Auto-Provision)**: Resolved `ERR_WAREHOUSE_ACCESS_DENIED` during dispatch/receive operations by implementing `ensure_transit_warehouse` in `SQLAlchemyInventoryRepository`. Virtual transit warehouses (deterministic UUIDv5) are now automatically created and assigned correct company ownership on-the-fly, satisfying Zero-Trust multi-tenancy requirements without manual DB seeding.
- **Persistence & Transaction Integrity**: Identified a high-priority bug where internal transfers (dispatches) returned success but failed to persist in the database. Injected `await session.commit()` in the FastAPI endpoints (`inventory.py`) to bridge the repository flush with the database commit.
- **Model Governance (Auth)**: Refactored `RefreshToken` in `auth_service` to inherit from `MultiTenantBase`. Migrated the database schema to include `tenant_id` and `group_id` for session persistence tokens, achieving 100% compliance in the architectural audit for the authentication microservice.
- **Status**: ✅ COMPLETED (Kardex Integrity Restored)

## [2026-03-31] - Phase 41.4: Multi-Tenant Zero-Trust Architecture (Receive Module initiated)
- **Architectural Plan Approved**: Finalized the high-fidelity design for the "Receive Transfer" (ICT-IN) module, ensuring 100% parity with standard entry documents.
- **Folio Persistence & Labeling**: Refactored the internal transfer architecture to generate an `InventoryDocument` during dispatch. This provides a formal folio (Audit Trail) and enables industrial label printing (Labels/Manifiesto) immediately upon dispatch.
- **In-Transit Lifecycle**: Extended the `DocumentStatus` enum to include `IN_TRANSIT`, `PENDING_RECEIPT`, `COMPLETED`, and `CLOSED`, guaranteeing formal tracking of stock while in virtual transit.
- **Status**: 🏃 IN PROGRESS (Implementation Plan approved)

---

## [2026-03-31] - Phase 41.3: Token Lifecycle & Session Persistence
- **Operational Continuity**: Expanded `ACCESS_TOKEN_EXPIRE_MINUTES` from 15 minutes to 720 minutes (12 hours) in `auth_service/app/core/config.py`. This update addresses UX friction for industrial operators by aligning session duration with a standard work shift, preventing mid-shift logouts while maintaining environment variable overrides for security flexibility.
- **Status**: ✅ COMPLETED

---

- **Anexo 24 / 30 Compliance Integration**: Engineered the UI rules for tracking mandatory cross-border trade elements. Incorporated `Customs Regime` (Temporal vs Definitivo) flags alongside an intelligent reactive `Pedimento Key` selector that filters available Customs keys (IM, AF, RT, A1, V1, EEI) to ensure tax compliance with Mexican SAT and US CBP regulations.
- **Visual Auditing**: Included visual "Vinculado" hints dynamically beneath parts involved in Cross-Border transfers. This prepares operators for auto-descargos algorithms (FIFO/PEPS) executed by the upcoming backend compliance microservices.
- **Micro-interactions & UX Constraints**: Polished layout inconsistencies impacting operators using touchscreen pads by standardizing identically tall (`140px`) bounding boxes across dynamic selection states (`industrial-card`), resolving padding deformations.
- **Architecture Integrity**: Successfully intercepted an Angular `NG5002` parser crash triggered by complex `@if` chunk unbalances inside destination cards, restoring perfect bundle compilations. Corrected `dispatch` 404 by properly mounting `inventory.router` into the FastAPI ecosystem.
- **Status**: ✅ COMPLETED

---

## [2026-03-31] - Phase 40: Inter-Company Logic & Industrial UX Hardening
- **Industrial Tap Interface**: Replaced standard native HTML `<select>` dropdowns in the Inventory Transfer module with high-contrast, scalable button "cards". This satisfies the UX requirement for factory/warehouse operators using touch devices under harsh lighting and wearing safety gloves.
- **Inter-Company Transfer Flow**: Formally decoupled target warehouse selection for Inter-Company operations. The UI now only requires selecting the Destination Company (Receiver), gracefully delegating physical warehouse selection to the inbound logistics team taking receipt of the transit.
- **CORS API Hardening**: Investigated intermittent `OPTIONS 400 Bad Request` exceptions by injecting `X-Silent-Error` and `X-Warehouse-ID` headers sequentially into FastAPI's CORS whitelists (`common/config.py`).
- **Database Cleansing**: Fired root diagnostic purges against `master_data_service` to eliminate ghost warehouses/companies, cementing the binary Matrix/Partner UI logic for MX and US.
- **Status**: ✅ COMPLETED

---

## [2026-03-30] - Phase 39: Binational Routing & Industrial Hierarchy (Golden Source Prep)
- **Zero-Trust Physical Contexting**: Shifted the transactional flow from a "Select Origin" paradigm to a "Define Current Context" paradigm. Transformed the module's main title into a robust, centralized Warehouse Selector predicting a physical operator's physical presence.
- **Binational Inter-Company Routing**: Solved the `company_id` visibility boundary. Matrix (`INTERNO-MX`) can now see Partner (`INTERNO-US`) active facilities to initiate transit (`SHIPPED`) bridging. The UI natively bifurcates payload calls between `initiateInterCompanyTransfer` and `dispatchInternalTransfer`.
- **Industrial Infrastructure & WIP**: Expanded `Location` and `Warehouse` models to track `is_production_resource` and logical hierarchy (Parent-Child containers). Frontend now decorates internal machinery with a `WIP RESOURCE` premium badge to differentiate them from storage racks.
- **Database Sanity**: Wiped legacy warehouse ghost records via atomic `seed.py` purges, injecting a fresh binational catalog.
- **Status**: ✅ COMPLETED

---

## [2026-03-30] - Dashboard Stabilization: Industrial Resilience & UI Focus
- **Industrial Resilience**: Refactored `InventoryService` with `Promise.allSettled` to prevent dashboard crashes on non-critical catalog failures (Categories/Brands).
- **Silent Error Interceptor**: Injected `X-Silent-Error` headers into secondary metadata requests to suppress redundant "Critical Failure" alerts for non-fatal backend misses.
- **UI Architecture**: Standardized "Mission Control" with a minimalist, borderless company selector, elevated z-index contexts (`z-20`), and removed redundant component-level selectors.
- **Device Optimization (iPad Pro)**: Calibrated title scaling (5xl/3xl) and implemented premium operational exit routes (Back to Dashboard) in ledger workflows.
- **Metadata Robustness**: Enhanced icon mapping logic to support diverse backend naming conventions (`IN/OUT`, `ENTRY/EXIT`, `ENTRADA/SALIDA`).
- **Status**: ✅ COMPLETED (v1.9.0 Hardened)

---

## [2026-03-29] - Viatra Core v0.9.5: Multi-Tenant Handshake & Dashboard Stabilization
- **Dashboard Stabilization**: Fixed 401 Unauthorized errors caused by Interceptor token overwriting.
- **Session Persistence**: Extended selection token lifespan to 24h for smoother session transitions.
- **UX Recovery**: Implemented Group Status fallback in `get_booking_status` to unlock Dashboard for demo users.
- **Bug Fixes**: Resolved `AttributeError` in Viatra Repositories.

## [2026-03-29] - Viatra Core Multi-Tenant Architecture Log
- **Microservice Integration**: `viatra-service` successfully integrated into the backend cluster. Standardized the global middleware so it mirrors the exact exceptions expected by the Angular frontend (status, message, meta).
- **Multi-Tenant Data Consistency**: Cleaned up the initial mock data scripts (`auth_service/scripts/seed.py`) to employ true `ON CONFLICT DO NOTHING`, guaranteeing that subsequent container restarts don't duplicate `user_company_roles` or trigger HTTP 500 exceptions in `InternoCoreGlobalMiddleware`. 
- **OAuth Handshake Lifecycle**: Adjusted the `SELECTION_TOKEN_EXPIRE_MINUTES` payload parameter to `1440` (24 hr) inside the auth container to natively support "switch-company" operations on the `viatra-frontend` via stored `sessionStorage` tokens, just like the old legacy monolithic login flow.


## [2026-03-29] - Viatra Core — Cluster Hardening & Certification (v0.8.5)
- **Hardening:** Reubicación de `viatra-service` a puerto **8011** y corrección masiva de imports SQLAlchemy (Composite Fix).
- **Inteligencia:** Despliegue de los centinelas `SkySentinel` y `StayGuardian` con automatización APScheduler.
- **Fintech Resilience:** Implementación de Periodo de Gracia (48h) en Webhooks y reporte certificado en PDF.
- **Validation:** Certificación de clúster mediante `smoke_test.py` con handshake Auth-Viatra validado.
- **Next:** Despliegue oficial a AWS (S3/CloudFront) y activación de Amadeus API Real-Time.

---


## 2026-03-29: Phase — Viatra Core Social Auth & Booking Engine Bridge
**Status:** ✅ Completed
**Focus:** Social Multichannel Auth, Zero-Trust Persistence, Mission Control UI.

### Technical Milestones
1. **Auth Microservice Expansion:**
   - Implemented `POST /api/v1/auth/social-login` supporting Google (PKCE/OIDC), Facebook, and Microsoft.
   - Enforced **Traveler Auto-Registration**: Social users without a tenant are automatically mapped to the "Viatra Core — Travelers" enterprise, ensuring P2P (Peer-to-Peer) access to trip groups.
   - Standardized `selection_token` handshake, maintaining the multi-tenant architectural integrity of the Interno Core ecosystem.
2. **Booking Engine Core (`viatra_service`):**
   - Implemented the **Zero-Trust Repository Pattern**: Every database query is implicitly filtered by `company_id` using the `BaseRepository` abstraction.
   - Designed financial invariants via `BookingService`: Trips cannot be persisted with a price ≤ 0, protecting the integrity of the future subscription module.
   - **Sentinel Readiness:** Injected `flight_number` tracking into `TravelerGroup` to enable real-time flight status monitoring in the next phase.
3. **Mission Control UI (Angular 19):**
    - Bootstrapped `viatra-frontend` in port `4201` with a high-premium "Slate-950 + Neon Cyan/Amber" visual language.
    - **High-Fidelity HUD Design**: Implemented the "Expedición Islandia 2026" glassmorphic timeline and mission control ledger.
    - **Styling Engine**: Integrated Tailwind CSS v3.4 and resolved PostCSS/Sass compilation order issues.
    - Integrated **Google GSI (Identity Services)** and session management for the social auth handshake.

**Next Immediate Goal:** Integrate **Stripe Billing** to generate monthly installment plans for traveler groups and activate the **SkySentinel Bot** for flight cost/status tracking.

---


## 2026-03-26: Phase 37 Implementation — HR & Physical Identity
**Status:** 🏃 In Progress
**Focus:** HR Microservice Bootstrap, Intracluster Auth Proxy, Kiosk Mode Hardware Buffer.

### Current Status
- Backend core (Auth, Inventory) is hardened and ready for physical identity integration.
- Phase 37 planning is finalized; execution begins with infrastructure setup (HR DB, HR Service Scaffold).
- Technical debt prioritized: Overhaul of `tickets_service` and IDempotent decorator implementation.

**Goal for Today:** Complete the HR Service bootstrap, DB initialization, and the Auth-HR secure proxy handshake.

---

## 2026-03-25: Phase 37 — HCM Engine & Industrial Hardening
**Status:** ✅ Completed
**Focus:** Physical Identity, Zero-Trust Ledger, Token Taxonomy

### Technical Milestones
1. **Auth Service Hardening (Replay Attack Mitigation):**
   - Implemented strict JWT Taxonomy (`typ` claims) separating access, refresh, and selection tokens.
   - Designed persistence for rotation: `refresh_tokens` are now stored as SHA-256 hex hashes in Postgres rather than raw strings to protect against DB leaks.
2. **Inventory Integrity (The "Sealed Price" Pattern):**
   - Locked financial transitions for Inter-Company Transfers via `unit_price_at_dispatch`.
   - Populated mandatory `tenant_id` invariants across Virtual Transit Warehouses guaranteeing multi-tenant data isolation.
3. **HR Microservice Architecture (HCM Engine):**
   - Mapped legacy `.NET` domains (Production, Quality, Gym, Outset) to abstract `Employee` concepts into a unified `hr_service` running on port `8004`.
   - Bootstrapped the architectural design of the "Phantom Link": Distributing `collaborator_id` implicitly using JWT `sub` and tracking operational UI scans.
   - Enforced physical identity mechanics: Kiosk-Mode Invisible Buffer (~500ms debounce), robust hashing (Bcrypt for PIN, SHA-256 for RFID indexing).
   - Designed Strict Hierarchy Context via Recursive CTEs tied through `supervisor_id` self-referential relations.

**Next Immediate Goal:** Spin up `hr-service` and `hr_db` via Docker, wire the Auth-Proxy Intracluster endpoint (`/api/v1/internal/collaborators/verify`), and execute the FastAPI DI extraction (`get_current_collaborator`) in the Inventory Service.

---

## 2026-03-16: Phase 36 — Multi-Tenant Consolidation
**Status:** ✅ Completed
- Reconciled hardcoded `company_id` UUIDs across backend microservices to match global constants (Enterprise, Logistics, Demo).
- Resolved global CORS preflight (`OPTIONS`) hurdles using optimized Starlette configurations.
- Integrated `master_seed.py` for atomic multi-service data staging (Catalog + Inventory levels).

---

*(Historical log clean-up performed to remove ANSI/binary corruption from earlier PowerShell runs)*

 # #   [ 2 0 2 6 - 0 3 - 3 0 ]   I n v e n t o r y   T r a n s f e r   F i n a l i z a t i o n   &   M u l t i - t e n a n t   R e f i n e m e n t 
 # # #   S u m m a r y 
 F i n a l i z e d   t h e   i n v e n t o r y   t r a n s f e r   o p e r a t i o n s   b y   i m p l e m e n t i n g   s t r i c t   t e n a n t - b a s e d   f i l t e r i n g   a n d   b i n a r y   r e g i o n a l   c l a s s i f i c a t i o n   ( M X / U S ) .   T h e   s y s t e m   n o w   c o r r e c t l y   d e t e c t s   b i n a t i o n a l   m o v e m e n t s   b e t w e e n   s e p a r a t e   l e g a l   e n t i t i e s   ( I n t e r n o   L o g i s t i c s   M X   v s   U S )   a n d   e n f o r c e s   c o m p l i a n c e   r i t u a l s . 
 
 # # #   T e c h n i c a l   M i l e s t o n e s 
 -   [ x ]   M u l t i - t e n a n t   w a r e h o u s e   s e l e c t o r s   ( F r o n t e n d ) . 
 -   [ x ]   W a r e h o u s e   A P I   m e t a d a t a   e x p a n s i o n   ( B a c k e n d ) . 
 -   [ x ]   I n t e r - c o m p a n y   s e e d   r e f a c t o r . 
 -   [ x ]   D a s h b o a r d   t e l e m e t r y   c i r c u i t   b r e a k e r . 
 
 # # #   S t a t u s 
 I n v e n t o r y   C o r e   i s   n o w   f u n c t i o n a l l y   c o m p l e t e   f o r   b a s i c   t r a n s f e r s .   N e x t   p h a s e :   T i c k e t s   &   O r d e r s   i n t e g r a t i o n .  
 
### [2026-04-01] - Binational Inventory Compliance (Phase 40 COMPLETE)
- **Status**: Successful three-leg ICT simulation (Enterprise TJ -> Log MX -> Log US) [3-User SoD Compliant].
- **Key Achievements**:
  *   Standardized Inter-Company Transfer (ICT) status reporting in **English** for international audit compliance.
  *   Validated **Multi-Leg Transfer Chain** with distinct users: Admin A initiates -> Op B receives & re-ships -> Super C receives (US).
  *   Enabled **Administrative Debt Pattern**: Blocked documents with missing price are now flagged for Finance post-processing without stopping operations.
  *   Implemented **Anexo 24 / FIFO Pedimento Propagation**: Ensuring full legal traceability across binational entities (Mirroring).

---

## [2026-04-03] - UI Consolidation & Industrial Readiness (Phase 41.5 COMPLETE)
- **Dynamic Binational Guard**: Implementada lógica inteligente basada en códigos de país (MX/US) en el frontend. Las transferencias locales entre empresas del grupo en MX ocultan automáticamente campos aduaneros.
- **Modo Permisivo Industrial**: Configuración del formulario en modo "Warning-Only". La falta de Pedimento o Tasa de Cambio genera alertas visuales pero NO bloquea la ejecución de la transferencia.
- **Unified Dispatch HUD**: Consolidación de indicadores en el sidebar "Resumen de Carga". Se profesionalizó la terminología a "Compliance Legal" (ADUANA) y se implementó lógica de estados dinámicos (PENDIENTE, LISTO, PERMISIVO).
- **Status**: ✅ COMPLETED (Frontend Ready for Warehouse Stress Test)

