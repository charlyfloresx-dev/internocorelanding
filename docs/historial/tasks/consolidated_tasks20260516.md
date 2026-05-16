# InternoCore: Consolidated Tasks (2026-05-16)

## Backlog Superado (Done) — Fases previas

- [x] **Industrial Auth & Menu Reconciliation**: Synchronized the frontend `NavigationService` with the backend `scopes` provided in the JWT.
- [x] **JWT Payload Hardening**: Patched `collaborator_login_command.py` to include `scopes` in the access token for industrial users.
- [x] **Kiosk Validation**: Updated `kiosk_auth_flow.py` to verify and decode JWT scopes in real-time.
- [x] **HCM Migration Sweep**: Added `hcm-service` to the unified migration orchestrator (`migrate_all.ps1`).
- [x] **Alembic HCM Sync**: Successfully applied `photo_path` and `user_id` migration to the `collaborators` table.
- [x] **Documentation Sync**: Executed `sync-docs.md` workflow, ensuring `REPO_LOG.md` and `SERVICE_LOG.md` are aligned with Phase 106.

## Backlog Superado (Done) — Sesión actual 2026-05-16 (Phase 107)

- [x] **Gateway CORS Fix**: Moved `add_header` directives out of `if` blocks in `nginx.conf`, restoring valid Nginx startup.
- [x] **Inventory StockRelocationCreate Schema**: Defined `StockRelocationCreate` Pydantic schema in `inventory_app/schemas/stock.py`.
- [x] **Unified Seed: Multi-DB Refactor**: Refactored `unified_industrial_seed.py` to create dedicated sessions per microservice database.
- [x] **Master Data Migration: `translation_key` en `movement_concepts`**: Applied migration `f21020a05ace`.
- [x] **Inventory DB Baseline (BLOCKER SOLVED)**: Implemented `000_inventory_baseline.py` with idempotent guards and exhaustive audit/multitenant columns.
- [x] **Inventory Seed Stabilization**: Updated `seed.py` to be parameter-less and deterministic. Verified clean bootstrap (DB drop + upgrade + seed).
- [x] **Notification Service Hardening**: Synchronized models with `MultiTenantBase` and fixed missing audit columns.
- [x] **Ecosystem Validation**: Executed `validate_ecosystem.ps1` and `generate_code_graph.py` with 100% compliance.
- [x] **Dead File Cleanup**: Removed `backend/scripts/create_all_tables.py` and deprecated `migrate_schema.py`.

## Pendientes Críticos (Phase 107 - Próximos pasos)

### P0 — Cross-Service Migration Stabilization
- [ ] **Tickets DB Baseline**: Replicate the "Inventory Baseline" pattern for `tickets_service` to ensure clean cold-starts.
- [ ] **Subscription DB Baseline**: Replicate baseline pattern for `subscription_service`.
- [ ] **Validate `migrate_all.ps1` on clean start**: Perform a full `docker-compose down -v` and run the orchestrator to certify 100% success.

### P1 — Seed & Data Integrity
- [ ] **Unified Industrial Seed (Final Sweep)**: Ensure all microservices (Tickets, Subscriptions) are populated by the master seed script.
- [ ] **Cross-Company Transfer Validation**: Perform a real `inter_company_transfer` via API to verify FIFO and WAC logic in the new schema.

### P2 — Funcional / Frontend
- [ ] **Subscription Service 500 Error**: Investigate failure during `select_company_command` in the subscription module.
- [ ] **Frontend Login Persistence**: Verify browser session correctly handles industrial JWT scopes after hard refresh.
- [ ] **Nginx `host not found` on startup**: Fix with `depends_on: service_healthy` conditions in `docker-compose.dev.yml`.

### P3 — Deuda técnica / Backlog
- [ ] **Mobile App Synchronization**: Re-validate Flutter `interno_billing_app` with updated JWT structure.
- [ ] **Customs Reporting**: Implement binational customs dashboard in frontend for US-MX transfers.
- [ ] **AuditBase Ledger Verification**: Verify that `transaction_id` is correctly propagated from Gateway to DB in every movement.
