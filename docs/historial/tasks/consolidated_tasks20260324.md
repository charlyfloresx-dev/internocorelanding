# Consolidated Tasks — 2026-03-24

## Project: Interno Core — Phase: Frontend Internationalization (i18n)

This snapshot summarizes the current state of completed, in-progress, and pending tasks from the frontend localization session.

### 🏆 Completed Today (Frontend i18n & Legacy Hardening)

-   [x] **Infrastructure**: Define `TranslationService` and Signal-based `TranslatePipe`.
-   [x] **Locale Handshake**: Synchronize `en.json` and `es.json` for core modules.
-   [x] **Main Layout**: Translate side-nav, header, and themes.
-   [x] **Auth / Login Module**: Full translation of the login flow, QR/RFID scanner, and forgot password.
-   [x] **Inventory Dashboard Module**: Translate metrics, charts, and movement ledger.
-   [x] **Product Catalog Module**: Translate product list, actions, and table headers.
-   [x] **User Management Module**: Translate role administration, permissions matrix, and invitations.
-   [x] **Bug Fix**: Resolve `NG5002` compilation error in `inventory-dashboard.component.ts`.
-   [x] **Zero-Trust Auth**: Refactored session restoration to validate synchronously via `auth_service` during `APP_INITIALIZER`.
-   [x] **Industrial Resilience**: Implemented `Cache-Then-Fallback` logic in master data and inventory telemetry via local storage interceptors to withstand WiFi disconnection.
-   [x] **Readiness Gatekeeper**: Active component logic blocking dashboard metrics unless `checkReadiness()` passes.
-   [x] **Idempotency Headers**: UUID v4 generation and injection tracking for POST/PUT/PATCH across the multi-tenant interceptor.
-   [x] **Audit Footer**: Implemented the Triple Identity view exposing folios vs UUIDs.

### 🚧 In Progress

-   [ ] **Global System Messages**: Replace hardcoded `toastService.info` strings in services with `translationService.translate`.
-   [ ] **Form Validators**: Localization of dynamic validation messages (Required, Email, MinLength).
-   [ ] **Module Audit**: Final walkthrough of `Production`, `Quality`, and `WMS` for remaining hardcoded strings.

### 📅 Next Phases (Backlog)

**Phase 1: Advanced Frontend Polish**
-   [ ] **Language Persistence**: Store the user's language preference in `localStorage` or backend profile.
-   [ ] **Skeleton Screens**: Localized "Loading..." states and empty results messages.
-   [ ] **Currency & Dates**: Internationalization of date formats and currency symbols based on the active locale.

**Phase 2: Backend - Master Data Sync**
-   [ ] **Error Code Homologation**: Refactor backend `HTTPException` calls to return language-agnostic codes (e.g., `ERROR_ITEM_NOT_FOUND`) for frontend translation.
-   [ ] **Master Seed V5**: Orchestrate seeding for additional demo companies with localized master data.

**Phase 3: AWS Deployment Strategy**
-   [ ] **ECR Repository**: Create the repository for the backend microservices.
-   [ ] **S3 + CloudFront**: Configure the bucket and CDN for the frontend standalone build.
-   [ ] **SPA Routing**: Configure CloudFront 404/403 redirects to `index.html`.

### 🚨 Known Issues

-   **Backend Linting**: Persistent Pyre2 linting errors in microservices (non-blocking for frontend focus).
-   **Terminal Noise**: esbuild warnings regarding unused components in the dashbord (requires code cleanup).
-   **Documentation Gap**: The `WMS` and `Production` modules have not been fully audited for hardcoded strings yet.
