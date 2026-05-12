# Master Implementation History — 2026-03-25

## Session 1: Industrial Auth Service Hardening
The authentication microservice was hardened to meet production-level security standards, specifically targeting multi-tenant isolation, precise session management, and AWS deployment readiness.

### Key Technical Decisions
1.  **JWT Taxonomy & Payload Hardening**:
    *   Added a `typ` claim to all tokens (`access`, `refresh`, `selection`). This is a critical security layer that prevents a long-lived Refresh Token from being used as a short-lived Access Token in case of extraction.
    *   Tokens are now explicitly bound to a `company_id` (except for the initial handshake), enforcing tenant isolation at the token level.
2.  **Refresh Token Rotation & Persistence**:
    *   A new `RefreshToken` model was created to track active sessions in the database.
    *   Instead of storing raw tokens, we store a **SHA-256 hex hash**. This protects the database if it's compromised.
    *   **Rotation Logic**: On each refresh, the old token is revoked, and a brand-new pair of tokens is issued. This provides **Token Replay Protection**.
    *   **Revocation Detection**: If a revoked token is used, it signals a potential replay attack, allowing for further audit actions.
3.  **Tenant & User Status Validation**:
    *   The refresh endpoint `/auth/refresh` performs real-time status checks. If a user is deactivated or a company is suspended, further refreshes are blocked immediately.
4.  **AWS Deployment Alignment**:
    *   Updated `config.py` to use environment-based secrets with local fallbacks.
    *   Configured tokens to have precise lifetimes (15 min access, 30 days refresh), ideal for secure mobile and web client sessions.

### Implementation Summary
- [x] Created `RefreshToken` model and registered it in SQLAlchemy.
- [x] Updated `app/core/security.py` with the new token taxonomy.
- [x] Updated `app/commands/select_company_command.py` to handle the dual token grant.
- [x] Implemented `POST /api/v1/auth/refresh` on `auth.py`.
- [x] Created and applied migration `d1a4f83cbe7a` after resolving a "multiple heads" conflict.
- [x] Verified token taxonomy and hashing logic with unit tests.

### Current Status
The Auth microservice is now ready for frontend integration and AWS deployment. Next phase will focus on the **Frontend Interceptor** update to handle the new token structure and automatic refreshes.

---

## Session 2: Inventory Audit & ICT Integrity

The inventory microservice was audited and hardened to ensure absolute financial consistency during multi-tenant transfers. The primary goal was to implement the "Price Freeze" (Sealed Price) pattern, ensuring that once a transfer is dispatched from Company A (TIJ), the acquisition cost for Company B (SDY) remains immutable regardless of any future changes in the Master Data price.

### Key Technical Decisions
1.  **Multi-Tenant Data Integrity (Hardened Isolation)**:
    *   **Mandatory `tenant_id` Enforcement**: Identified and corrected a regression where `InventoryDocument` and `Movement` models were missing the `tenant_id` field in certain programmatic flows.
    *   **Virtual Transit Warehouse (Isolation)**: Refined the deterministic creation of the "Virtual Transit Warehouse" (uuid5-based). Ensured it is correctly assigned to the **destination company's tenant**, creating a secure "Trusted Broker" between companies.
2.  **The "Sealed Price" Pattern (Financial Invariants)**:
    *   **Price Capture at Dispatch**: Modified `TransferCommandHandler` to capture the `unit_price_at_dispatch` at the exact moment of the `TRANSFER_OUT`.
    *   **Inbound Price Locking**: The `TRANSFER_IN` logic in Company B now uses the `unit_price_at_dispatch` from the ICT document, protecting Company B's WAC from fluctuations in Company A's catalog during transit.
    *   **Audit Mirroring**: Automatic creation of `InventoryDocument` mirrors (Draft) in Company B upon dispatch, enabling real-time visibility ("seeing the cargo") before official reception.
3.  **Audit Forensics (The Price Freeze Test)**:
    *   Created `scripts/verify_sealed_price.py` to automate the validation of the entire ICT life cycle.
    *   The test simulates a complete cross-company flow: Dispatch (A) -> Transit -> Receipt (B).
    *   **Success Criterion**: The final WAC increment in Company B must match the price pactado at dispatch, even if the "market price" is simulated to change in between.

### Implementation Summary
- [x] **Hardened `TransferCommandHandler`**: Populated `tenant_id` in all entity creations (Warehouses, Documents, Movements).
- [x] **Corrected `InventoryRepository`**: Ensured `InventoryLevel` creation always includes `tenant_id`.
- [x] **Refined `seed.py`**: Cleaned up the demo data to include mandatory `tenant_id` and `external_reference` fields.
- [x] **Created `verify_sealed_price.py`**: A robust audit script to verify transaction integrity.
- [x]  **Resolved Unique Constraint Conflicts**: Fixed a bug where outbound and mirror documents shared the same `external_reference`, causing a database collision.

### Results
- ✅ **TEST PASSED**: "The Price Freeze Test" confirmed that the acquisition cost in Company B is $12.00 (pactado) and not affected by external mutations.
- ✅ **DATA INTEGRITY**: All new inventory records now strictly comply with the `NOT NULL` constraints for `tenant_id`.

---

## Session 3: Architecture for HR Microservice (Phase 37)

### Technical Achievements & Architecture Evolution
- **Frontend Concepts Parsing**: Fixed how `inventory-document.component.ts` parses the `type` returned by `master-data-service` (ENTRY, OUTPUT) alongside legacy tags (IN, OUT, ENTRADA, SALIDA). This resolved the empty dropdown.
- **Collaborator / HR Service Phase 37 Inception**: Evaluated the legacy `.NET` logic for Human Resources (`Employee.cs`, `Labor.cs`). Concluded that placing physical identity login logic and credentials inside the core Auth Service violated SRP (Single Responsibility Principle) and coupled independent domains.
- **Microservice Redesign**: Finalized the decision to build a new `hr_service`.
  - Auth Service will proxy the login (`/api/v1/auth/collaborator/login`) receiving the RFID or PIN to generate the JWT internally.
  - HR Service handles the physical identity matching via a secure internal endpoint with strict timeouts (2-3s).
  - JWT Claims will carry `sub`, `cid`, `role: collaborator`, and `wid` with a shift-based expiration (8-12 hours).
- **Physical Identity Security**: Drafted `rfid_tag` hashing (SHA-256 with static application salt) and database indexing for $O(1)$ scans in physical hardware, while `pin_code` will utilize robust `Bcrypt`.
- **Architectural Hierarchy**: `supervisor_id` established as a strict self-referential ForeignKey (`Collaborator.id`) to enable Recursive CTEs for reporting structures.
- **Kiosk Mode UI**: Proposed an "invisible keyboard buffer" via Angular `@HostListener` to automatically sink high-speed scanner outputs terminating in 'Enter', utilizing a ~500ms debounce/cleanup timer to prevent misreads.

### MVP Integration: Inventory Service & Traceability
To ensure the transition remains decentralized (Phantom Link pattern), the following invariants were mandated:
- **Distributed Identity (Phantom Link)**: `collaborator_id` added as a Nullable and Indexed UUID to `Movements`. Nullable usage preserves operations triggered by administrative system users lacking physical presence.
- **Identity Injection Middleware**: Created a robust FastAPI Dependency injection `get_current_collaborator` isolating the extraction of the `sub` claim. 
- **Warehouse Lock (Context Validation)**: Strict zero-trust barrier verifying that a physical operator recording a scan within a warehouse strictly matches the `wid` in their Token (403 Forbidden on violation).
- **Floor Feedback (Quick-Audit Endpoint)**: Designed `/recent-by-collaborator/{id}` to bounce back the 10 most recent scanned items towards the Kiosk UI for visual peace-of-mind confirmation during high-volume sessions.

### Blockers Resolved
- The attempt to squeeze identities straight into Auth Service was halted and quickly pivoted based on the user's domain-driven insights, keeping Auth strictly as an Identity Provider and token issuer.

### Next Immediate Steps
1. Add `hr-service` and `hr_db` (postgres:15-alpine) to `docker-compose.yml` and initialization scripts.
2. Bootstrap `hr_service` and its Models & Repositories (`Collaborator` inheriting `MultiTenantBase`).
3. Wire the intracluster HTTP proxy logic from `auth_service` to `hr_service`.
