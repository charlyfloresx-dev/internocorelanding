# InternoCore: Consolidated Tasks 2026-05-01

## Tickets Service Industrialization
- [x] Correct Dependency Injection in `ticket_routes.py`.
- [x] Synchronize database tables for Tickets, History, Comments, Outbox, and EscalationRules.
- [x] Implement Phase 6 Notifications (TicketCreated, TicketStatusChanged) via Outbox.
- [x] Implementation of Phase 7 Dynamic Escalation Matrix (Multi-tenant).
- [x] Create functional `EscalationWatcher` script.
- [x] Implement Phase 8 Preview: AI Support Center integration in `TicketService`.
- [x] 100% Code Graph Compliance for `tickets_service`.
- [ ] Persist `tickets-escalation-worker` in `docker-compose.yml`.
- [ ] Implement `while True` loop in `escalation_watcher.py`.
- [ ] Integrate with `notification_service` via Outbox delivery.

## Master Data Industrialization
- [x] Refactor `WarehouseFormComponent` to SideDrawer & Industrial UI.
- [x] Refactor `ConceptFormComponent` to SideDrawer & Industrial UI.
- [x] Fix TypeScript errors in `PartnerCatalogComponent` (DrawerOptions).
- [x] Migrate `ConceptCatalogComponent` to `SideDrawerService`.
- [x] Resolve template syntax and visibility errors in Master Data forms.
- [x] Standardize `SideDrawerService` integration across all catalog modules.

## Documentation & Compliance
- [x] Run `generate_code_graph.py` and resolve violations.
- [x] Update `REPO_LOG.md` with Phase 76 progress.
- [x] Sync documentation using `sync-docs.md` workflow.
- [x] Generate Backend Status Report (`backend_status_report_20260501.md`).
- [x] Generate Frontend Status Report (`frontend_status_report_20260501.md`).
