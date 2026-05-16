# InternoCore: Master Implementation History (2026-05-16)

## Architectural Phase: 106 - Industrial Auth & Menu Reconciliation

### Objective
Align the industrial authentication flow (RFID/PIN) with the administrative menu architecture to ensure that warehouse operators have immediate and persistent access to inventory modules without manual role mapping in the frontend.

### Implementation Details

#### 1. Backend: JWT Payload Extension
- **Service**: `auth_service`
- **File**: `collaborator_login_command.py`
- **Change**: Injected the `scopes` claim into the JWT payload during the `collaborator_login` handshake.
- **Rationale**: The frontend `NavigationService` filters sidebar items based on `scopes`. By including them in the JWT, we eliminate the need for the frontend to "guess" or "mock" permissions for industrial users, ensuring a single source of truth (SSOT).

#### 2. Backend: Validation Suite Upgrade
- **Script**: `kiosk_auth_flow.py`
- **Feature**: Added JWT decoding logic using `PyJWT` (with signature verification bypass for testing) to print and verify that the `scopes` claim is correctly propagated.
- **Verification**: Successfully validated identities for Carlos (Supervisor), Luis (Supervisor), and Ana (Operator).

#### 3. Infrastructure: Unified Migration
- **Script**: `migrate_all.ps1`
- **Change**: Added `interno-hcm-dev` to the service sweep.
- **Rationale**: Ensures that HCM migrations (like the recent `collaborator` table updates) are part of the automated dev environment initialization.

### Technical Decisions
- **Scope vs Permission**: Maintained the distinction where `permissions` represent low-level industrial actions (READ/WRITE/SCAN) and `scopes` represent high-level UI module access. Both are now present in the JWT for comprehensive access control.
- **T1/T2 Bypass**: Confirmed that for Kiosk users, the system correctly bypasses the `selection_token` (T1) and issues a full `access_token` (T2) directly when exactly one company matches the identity.

### Environment Status
- **Postgres**: Clean schema with `alembic_version_hcm` synchronized.
- **Auth Service**: Operational with Phase 106 patches.
- **Frontend**: NavigationService logic verified and ready for industrial JWT consumption.
