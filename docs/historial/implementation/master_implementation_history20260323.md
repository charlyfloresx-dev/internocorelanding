# Implementation History: Zero Trust & Menu Resilience (2026-03-23)

## 🛠️ Summary of Actions

Today's focus was on hardening the authentication layer and ensuring UI resilience across the "Interno Core" ecosystem.

### 1. Zero Trust Authentication Guard
- **Problem**: Users reported that clearing browser cache didn't redirect to login, and the menu would sometimes "disappear" due to race conditions between session restoration and navigation.
- **Solution**: Implemented a **Zero Trust** strategy in `auth.guard.ts`.
    - The guard now performs a **direct synchronous check** of `localStorage` (`auth_session` and `_ic_auth_ctx`) before allowing any route activation.
    - If storage is missing or tokens are compromised, it triggers an immediate `logout()` and redirects to `/login`, regardless of the in-memory Signal state.
- **Service Refinement**: Updated `AuthService.restoreSession()` to ensure Signals are populated **synchronously** during the app initialization phase, preventing the "missing menu" flicker.

### 2. Multi-Tenant Interceptor & Idempotency
- **Idempotency**: Injected `X-Correlation-ID` (UUID v4) into every outgoing request via `MultiTenantInterceptor`. This ensures backend idempotency and enables forensic tracing of transactional chains.
- **Resilience**: Added a `catchError` circuit-breaker to the interceptor specifically for auxiliary services (e.g., `CurrencyService`). If an auxiliary service returns a 5XX error, the UI no longer blocks or forces a logout; instead, it logs a warning and allows the core application to function with fallbacks.

### 3. Unified CORS Policy
- Synchronized `CORSMiddleware` across all microservices (`auth`, `inventory`, `master_data`, `currency`).
- Explicitly allowed and exposed high-entropy headers: `X-Company-ID`, `X-Trace-Id`, `X-Transaction-ID`, `X-Correlation-ID`, and `Authorization`.

### 4. User Journey Validation (5 Pillars)
- **Pillar 1 (Identity)**: Confirmed that `DashboardService` correctly resets telemetry and state signals upon `activeCompanyId` changes (Hot-switching).
- **Pillar 3 (Golden Path)**: Validated the "Pedimento" legal requirement for binational transfers. The UI dynamically toggles the mandatory field based on `originCountry != targetCountry`.
- **Pillar 4 (Red Tag)**: Verified the "Confirm Receipt" modal logic for discrepancy handling (splitting quantities into Received vs Damaged).

## 📐 Architectural Decisions
- **Decision**: Synchronous Storage over Reactive Signals for Guards.
- **Rationale**: Signals are excellent for UI reactivity but can suffer from micro-delays during bootstrap. Guards requiring 100% security must verify the underlying persistence layer (`localStorage`) to prevent unauthorized "ghost" sessions.

## 🚀 Next Steps
- Transition to **Phase 35: AWS Infrastructure**. 
- Deploy microservices to **Amazon ECR** and configure **CloudFront** for the Angular frontend.
- Implement the **Corporate Valuation Dashboard** (Total Assets MXN/USD).
