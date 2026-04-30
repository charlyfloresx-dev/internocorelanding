# Master Implementation History - 2026-04-30
## Architecture: Reactive Industrial Subscription Guard

### 1. Subscription-Aware Identity (Auth Service)
We evolved the identity provider from a simple authentication service to a subscription-aware gatekeeper. 
- **Pattern**: Zero Trust Hydration.
- **Implementation**: The `auth_service` now fetches subscription metadata during token generation and refresh. Claims are embedded in the JWT to allow decentralized enforcement at the edge (API Gateways/Middlewares).

### 2. Layer 7 Enforcement (Global Middleware)
Access control is now enforced at the middleware layer using the JWT claims.
- **Logic**: 
  - `status == UNPAID` -> Block all traffic (Global Lock).
  - `status == RESTRICTED` or `readonly == true` -> Block non-safe methods (POST, PUT, DELETE).
- **Benefit**: Zero-latency enforcement without per-request database lookups for subscription state.

### 3. Sensory Reactivity (Angular 19 Signals)
The frontend uses a pull-based reactive model via Signals to synchronize UI state with the session.
- **Paywall Component**: A high-z-index overlay in the `AppComponent` that listens to the `isUnpaid` signal.
- **Banner Feedback**: Components like `InventoryDocument` use `isReadOnly` to trigger visual warnings and disable form submissions.

### 4. Forensic Auditing
- **Audit Script**: `audit_subscription_states.py` provides a suite of functional tests that simulate different subscription states and verify backend response codes (200 OK vs 402 Payment Required).
