# Consolidated Tasks — 2026-03-25

## Backend — Auth Service Hardening (Completed)
- [x] [PLANNING] Research current JWT and AWS configuration
- [x] [PLANNING] Design refresh token persistence (Model/Repo)
- [x] [EXECUTION] Create `app/models/refresh_token.py` and migration
- [x] [EXECUTION] Update `app/core/config.py` for AWS environment and lifetimes
- [x] [EXECUTION] Update `app/core/security.py` with `typ` claims and lifetime constants
- [x] [EXECUTION] Update `app/commands/select_company_command.py` to generate & persist refresh tokens
- [x] [EXECUTION] Implement `POST /refresh` with rotation and status checks
- [x] [VERIFICATION] Verify with `pytest` (Token taxonomy & hashing logic)
- [x] Update `common/infrastructure/models/base.py` for `AuditBase` consistency
- [x] Register new models in a clean migration history (Resolved multiple heads)

## Backend — Inventory Microservice Hardening (Completed)
- [x] **Phase 36: Audit Zero-Trust of the Inventory**
    - [x] Corrected `InventoryLevel` creation to include mandatory `tenant_id`.
    - [x] Fixed `TransferCommandHandler` to include `tenant_id` in Virtual Transit Warehouse and mirrored `InventoryDocument`.
    - [x] Implemented absolute "Price Freeze" (Sealed Price) for ICT.
    - [x] Finalized and executed `verify_sealed_price.py` test.
    - [x] Fixed `UniqueConstraint` on `external_reference` for mirrored documents.
- [x] **Base Seeding & Cleanup**
    - [x] Corrected `seed.py` to populate `tenant_id` and `external_reference` in `InventoryDocument`.
    - [x] Verified consistent UUIDv5 usage for deterministic IDs (Warehouses, Products, UOMs).

## Upcoming Phases (Backlog)

### Phase 37: HR Microservice & Physical Identity
#### Infrastructure & Databases
- [ ] Add `hr_db` to `init-multiple-databases.sh`.
- [ ] Create `hr-db` integration using `postgres:15-alpine` in `docker-compose.yml`.
- [ ] Spin up `hr-service` bounded to Internal Port 8000 (External 8004).

#### Backend: HR Service (New)
- [ ] Scaffold `hr_service` mirroring the layout of `subscription_service`.
- [ ] Implement Domain Entity `Collaborator` inheriting `MultiTenantBase`.
  - Properties: `internal_id`, `first_name`, `last_name`, `home_warehouse_id`.
  - Hierarchy: `supervisor_id` (Self-referencing ForeignKey to `Collaborator.id` for CTEs).
  - Hardware Properties: `rfid_tag` ($O(1)$ SHA-256 Hashed with static salt, Indexed), `pin_code` (Bcrypt Hashed).
- [ ] Seed script for demo collaborators.
- [ ] Internal Endpoint `/api/v1/internal/collaborators/verify` protected by Internal API Key for Auth Proxy.

#### Backend: Auth Service (Token Issuer)
- [ ] Create HTTP adapter for internal microservice queries (with 2-3s timeouts).
- [ ] Endpoint `/api/v1/auth/collaborator/login` (Expects RFID or PIN).
- [ ] Generate standard structure JWT with `role: collaborator`, `wid`, `cid`, Custom Expiration (8-12 HRS).

#### Backend: Inventory Service (MVP Traceability)
- [ ] Migration: Add `collaborator_id` (Nullable UUID, Indexed) to Movement schema.
- [ ] Implement FastApi Dependency `get_current_collaborator` to automatically extract `sub` and inject physical identity via Command Handler.
- [ ] Implement Context Validation **(Warehouse Lock)**: Reject transactions (403 Forbidden) if the payload's `warehouse_id` does not strictly match the `wid` extracted from the JWT (unless global Supervisor).
- [ ] Create Quick-Audit Endpoint `GET /api/v1/movements/recent-by-collaborator/{id}` limiting to the last 10 movements for immediate visual feedback on the floor.

#### Frontend: Hardware Integration
- [ ] `KioskLoginComponent` Layout.
- [ ] Implement `Invisible Keyboard Buffer` to intercept RFID string seamlessly from ZKTeco. Include a ~500ms debounce/cleanup timer to discard partial or dirty scans.

### Phase 38: Frontend Handshake & Hardening
- [ ] Update `AuthInterceptor` to support `typ` claim.
- [ ] Implement `refreshTokenSubject` for concurrent request queuing.
- [ ] UI feedback for "Session Expired" vs "Access Denied".

### Phase 39: AWS Resource Definition (Terraform/CloudFormation)
- [ ] Define ECR repositories for all backend services.
- [ ] Create ECS Task Definitions (Fargate).
- [ ] Configure Secrets Manager for `CORE_SECRET_KEY`.
- [ ] Set up S3 + CloudFront for frontend static hosting.

### Phase 40: Session Garbage Collector
- [ ] Task to purge expired refresh tokens periodically.
- [ ] Integration with AWS Lambda or ECS Scheduled Task.

## Technical Debt / Guardrails
- [ ] Implement `@idempotent` decorator on `CompleteTransfer` endpoint.
- [ ] Multi-currency conversion for cross-border ICT (MXN ⇄ USD).
- [ ] Add `InventoryService` logic to handle "Partial Receipt" (damaged items) in Empresa B.
- [ ] **[CRITICAL ARCHITECTURE]** Eradicate Root Pollution: Delete/move `patch_cors.py` from `backend/` root.
- [ ] **[CRITICAL ARCHITECTURE]** Refactor `subscription_service`: Remove `INFRASTRUCTURE_LEAK_VIOLATION` in `billing_service.py` and `webhook_service.py` by abstracting `IPaymentProvider` to a Domain Interface.
- [ ] **[CRITICAL ARCHITECTURE]** Overhaul `tickets_service` (0% Clean Arch Score):
  - Eradicate `HIDDEN_TRANSACTION_VIOLATION` by removing manual `.commit()` calls in `ticket_service.py` and `ticket_commands.py` (Migrate to UnitOfWork).
  - Remove direct SQLAlchemy ORM imports (`app.models.*`) from the Service/Command layers.
  - Fix Infrastructure boundary bleed by abstracting `HttpInventoryClient`.
