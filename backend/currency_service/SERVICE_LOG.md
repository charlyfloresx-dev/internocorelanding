# Service Log - Currency Service

## Architecture Overview
The Currency Service is a specialized microservice responsible for managing exchange rates and providing real-time valuation data to the Interno Core ecosystem.

## Technical Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL (currency_db)
- **ORM:** SQLAlchemy (Async)
- **Rate Provider:** Banxico (Bank of Mexico) API.

## Implementation Details

### 1. Multi-tenant Awareness
The service operates within the shared holding context, ensuring that rates are consistent across all companies mapped to the same business group.

### 2. External Provider Synchronization
- **Banxico Client:** Implemented with resilience and caching to avoid rate-limiting.
- **Data Model:** Stores historic and active rates in the `currency_exchange_rates` table.

### 3. API Handshake (2026-03-19)
- **Endpoint:** `GET /active-rate`
- **Output:** Returns the active conversion rate (USD to MXN) with timestamps.
- **Frontend Integration:** Directly consumed by the Angular `CurrencyService` to drive real-time valuation updates in the UI.

### 4. Shared Infrastructure
- **CurrencyClient:** A core utility provided in `common/infrastructure` that allows other services (Inventory, WMS) to fetch the latest rates without direct database access.

### 2026-04-14: Dependency Injection Fix (Critical) ✅
- **Resolution**: Fixed `AttributeError` in `get_active_rates` and `get_exchange_rates_summary`.
- **Architectural Cleanup**: Properly instantiated `SQLAlchemyCurrencyRepository` in the FastAPI dependency resolver. Previously, the raw `AsyncSession` was being passed to the service as a repository, causing runtime failures when fetching latest verified rates.
- **Impact**: Restored stability to the global currency valuation system used by the frontend and inventory modules.

### 2026-03-23 (Session 2): Rate Generation Robustness & Schema Mapping
- **Schema Validation**: Resolved HTTP 500 error triggered by missing PostgreSQL Table mappings `currency_exchange_rates`. Deployed a runtime initialization check using `Base.metadata.create_all`.
- **Banxico Client**: Hardened API parsing algorithm targeting SF43718 (USD->MXN FIX Rate). Rewrote `rate_provider.py` to seamlessly execute extraction under strict custom headers using custom `.env` secret variables `Bmx-Token`.
- **Frankfurter Fall-back Rule**: Added zero-latency transition system switching to the `Frankfurter` open banking API whenever external rate endpoints drop connection or deny token permissions.
- **Audit Compliance**: Modified FastAPI configuration adding `X-Correlation-ID` directly onto global expose/allow CORS layers ensuring resilient UI telemetry reporting.

### 2026-03-23: CORS & Resilience Synchronization
- **CORS Update**: Sincronizado `CORSMiddleware` para soportar headers de auditoría (`X-Trace-Id`, `X-Correlation-ID`).
- **Resilience**: El microservicio ahora reporta estados de salud compatibles con el nuevo `MultiTenantInterceptor` del frontend, permitiendo fallos agraciados (fallbacks) en lugar de bloqueos de UI.

### 2026-03-19: Initial Deployment
- Established microservice structure using the project-wide clean architecture.
- Successfully synchronized initial rates from Banxico for USD/MXN.
- Enabled cross-origin requests for the new Dockerized frontend.
- Verified connectivity with `currency_db` container.
