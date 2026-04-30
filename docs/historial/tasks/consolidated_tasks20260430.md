# Consolidated Tasks - 2026-04-30
## Phase 19/74: Subscription Lockdown & Grace Period

### ✅ Completed Tasks
1.  **Backend: Subscription Synchronization**
    - [x] Standardized JWT claims: `status` and `readonly`.
    - [x] Refactored `AuthService` to include `get_subscription_context`.
    - [x] Updated `/select-company`, `/refresh`, and `/me` endpoints for Zero Trust validation.
    - [x] Integrated `SubscriptionClient` to fetch real-time entitlements.
2.  **Frontend: Reactive UI Lockdown**
    - [x] Implemented `isReadOnly` and `isUnpaid` signals in `AuthService.ts`.
    - [x] Added `MultiTenantInterceptor` logic for `402 Payment Required` handling.
    - [x] Created Global Paywall overlay in `App.ts` for `UNPAID` status.
    - [x] Added `RESTRICTED` mode UI (banner + disabled buttons) to `InventoryDocumentComponent`.
3.  **Auditoría & Compliance**
    - [x] Executed `audit_subscription_states.py` (5/5 PASSED).
    - [x] Verified `generate_code_graph.py` (100% Compliance).
    - [x] Synchronized `REPO_LOG.md` and `SERVICE_LOG.md` across microservices.

### ⏳ Pending Backlog
- [ ] Implement manual Stripe webhook trigger validation once CLI is downloaded.
- [ ] Replicate `isReadOnly` logic in the **MES (Production)** module.
- [ ] Add "Pay Invoice" link to the Paywall overlay.
