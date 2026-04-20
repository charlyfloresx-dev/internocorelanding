# Consolidated Tasks - 2026-03-19

## Task Backlog Summary: Currency Integration & Frontend Stabilization

Review of the completed and pending tasks across all domains as of March 19th, 2026.

### ✅ Completed Tasks

#### 1. Backend: Currency Service (Domain: `currency_service`)
- [x] Design and implement `CurrencyExchangeRate` model in `common/models`.
- [x] Create core microservice `currency_service` with FastAPI.
- [x] Add active rate lookup endpoint (`/active-rate`).
- [x] Integrate `CurrencyClient` in the `common` infrastructure.
- [x] Ensure correct DB migrations in `currency_db`.

#### 2. Frontend: Infrastructure & Currency UX (Domain: `frontend`)
- [x] Rename `temp_future` to `frontend`.
- [x] Implement `CurrencyService` with Angular Signals.
- [x] Create `CurrencyFormatPipe` for dynamic formatting based on selected currency.
- [x] Update `InventoryDashboard` valuation widgets.
- [x] Integrate Unit Price/Subtotal fields in `InventoryDocument`.
- [x] Added `Total Value` calculation in `InventoryDocument` footer.
- [x] Display movement valuations in `InventoryDocuments` list.
- [x] Include financial details in PDF/Print templates (Invoice/Ticket).
- [x] Create Currency Selector in `MainLayoutComponent`.

#### 3. DevOps & Orchestration (Domain: `devops`)
- [x] Dockerize the frontend using Nginx.
- [x] Configure `environment.ts` in the frontend pointing to Docker-exposed ports.
- [x] Add `.dockerignore` to the frontend for efficient builds.
- [x] Link `frontend` container in `docker-compose.yml`.
- [x] Fix production build issues by disabling SSR/Prerendering.

### 🚧 In Progress

#### 1. Backend: Common Infrastructure (Domain: `common`)
- [ ] Stabilize `conftest.py` in `inventory_service` and `currency_service` to resolve mock import errors.
- [ ] Unit/Integration tests for `CurrencyClient`.

### 📅 Pending Tasks (Next Phase)

#### 1. Inventory Refinement
- [ ] Financial validation before processing documents (warn if price is 0).
- [ ] Audit logs for currency changes during document creation.

#### 2. Master Data Service
- [ ] Add base price retrieval to `MasterDataService` to pre-fill unit prices on product selection more reliably.

#### 3. UX/UI Polish
- [ ] Currency-aware history charts in the dashboard.
- [ ] Multi-currency support in the WMS logistics view.

---
**Current Milestone:** 🚀 Frontend is live and currency-enabled. Backend services are fully orquestrated in Docker.
