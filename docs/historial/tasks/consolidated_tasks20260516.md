# InternoCore: Consolidated Tasks (2026-05-16)

## Backlog Superado (Done)
- [x] **Industrial Auth & Menu Reconciliation**: Synchronized the frontend `NavigationService` with the backend `scopes` provided in the JWT.
- [x] **JWT Payload Hardening**: Patched `collaborator_login_command.py` to include `scopes` in the access token for industrial users.
- [x] **Kiosk Validation**: Updated `kiosk_auth_flow.py` to verify and decode JWT scopes in real-time.
- [x] **HCM Migration Sweep**: Added `hcm-service` to the unified migration orchestrator (`migrate_all.ps1`).
- [x] **Alembic HCM Sync**: Successfully applied `photo_path` and `user_id` migration to the `collaborators` table.
- [x] **Documentation Sync**: Executed `sync-docs.md` workflow, ensuring `REPO_LOG.md` and `SERVICE_LOG.md` are aligned with Phase 106.

## Pendientes (Backlog)
- [ ] **Frontend Login Persistence**: Verify that the browser session correctly handles the industrial JWT scopes after a hard refresh.
- [ ] **Mobile App Synchronization**: Re-validate the Flutter `interno_billing_app` with the updated JWT structure to ensure its internal RBAC is also aligned.
- [ ] **Performance Audit**: Monitor `kiosk_service` latency under heavy RFID scanning load (Simulated).
- [ ] **Customs reporting**: Implement the binational customs dashboard in the frontend for US-MX transfers.
