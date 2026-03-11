# Tickets Service Log

## Overview
The InternoCore Tickets Service evolved from a generic helpdesk module to the **Operational Motor** of the enterprise architecture (Phase 10). It orchestrates actions between users, production floors (MES), and inventory control (ERP).

### Service Stats
| Metric | Value |
|---|---|
| **Source Files** | 23 |
| **Data Models** | 6 (Ticket, Comment, History, Resource, StopLog, OutboxEvent) |
| **API Endpoints** | 6 REST |
| **Test Coverage** | 0% |
| **Last Audit** | 2026-03-08 |

---

### Completed Phases

#### Phase 9: Intelligence & Notifications
- **Status**: Completed (2026-03-04)
- **Features**:
  - P1-P4 priority mappings.
  - `TicketsClient` consumption of auto-generated events from the `inventory_service` (Stock Breaks, Low Stock).
  - SHA256 anti-fatigue debouncing logic inside the internal ticket creator to prevent duplicates during storms.
  - Basic Webhook Provider routing (later migrated to Notification Service).

#### Phase 10: Enterprise Orchestration (MES/ERP Migration)
- **Status**: Completed (2026-03-04)
- **Features**:
  - Extracted Webhook dispatch and notifications into a separate decoupled `notification_service`.
  - Added operational tracking parameters (`module_origin`, `area`, `estimated_time`, `real_time_spent`, `cost_estimate`).
  - Added foreign weak-link entities: `TicketResource` (Inventory coupling) and `StopLog` (Production OEE coupling).
  - Implemented the Outbox Pattern (`OutboxEvent` & `OutboxWorker`) to asynchronously push `TicketCreatedEvent` contracts over HTTP without tight blocking.
  - Created CQRS-style Handlers (`CreateTicketCommand`, `ConsumeResourcesCommand`).

#### Phase 16: Industrial Strengthening & Sanitization ✅
- **Status**: Completed (2026-03-05)
- **Sanitization**: Resolved **12 governance violations** (Root pollution moved, Multi-tenant models updated, Audit integrated).
- **Compliance**: `AuditService.track` integrated in `TicketCommandHandler` for professional forensic auditing.

---

### Audit Report (2026-03-08)

#### 🔴 Critical Bugs Found (3)
1. **`outbox_worker.py`**: Import from non-existent `app.db.session` — should be `app.dependencies.database`.
2. **`integration_events.py`**: Missing `import uuid` module — `uuid.uuid4` reference on line 13 will crash at runtime.
3. **`ticket_routes.py`**: Orphan `@router.post("/internal")` decorator on line 22 with no handler function — causes silent double-registration of `POST /`.

#### 🟡 Technical Debt (7 items)
| # | Item | Severity |
|---|---|---|
| D1 | `ConsumeResourcesCommand` doesn't dispatch to Kardex | 🔴 High |
| D2 | `AuditService.log_action` is a stub (console `print()`) | 🟡 Medium |
| D3 | Zero test coverage — no `tests/` directory exists | 🔴 High |
| D4 | No Alembic migrations | 🟡 Medium |
| D5 | `reference_code` COUNT() not scoped by `company_id` — multi-tenant collision | 🟡 Medium |
| D6 | `TicketRead` DTO missing `history`, `resources`, `stop_logs` | 🟡 Medium |
| D7 | `OutboxWorker` URL hardcoded to `localhost:8008` | 🟡 Medium |

#### ✅ Architecture Validated
- **CQRS Pattern**: Working (`CreateTicketCommand`, `ConsumeResourcesCommand`).
- **Outbox Pattern**: Implemented (`OutboxEvent` → `OutboxWorker`), aside from broken import.
- **SHA256 Debouncing**: Active and correctly hashing `company_id + warehouse_id + product_id + priority`.
- **Multi-Tenant Compliance**: All 6 models inherit `MultiTenantBase`.
- **API Response Format**: `{status, data, message, meta}` compatible with Angular frontend interceptor.

---

### Phase 1: Critical Bug Fixes & Multi-Tenant Blindaje ✅
- **Status**: Completed (2026-03-08)
- **Fixes Applied**:
  - ✅ **Bug 1**: `outbox_worker.py` — Fixed broken import `app.db.session` → `app.dependencies.database`.
  - ✅ **Bug 2**: `integration_events.py` — Added missing `import uuid` for `uuid.uuid4()` default_factory.
  - ✅ **Bug 3**: `ticket_routes.py` — Implemented `create_internal_ticket` handler for orphan `/internal` decorator with SHA256 debouncing + `X-Company-ID` / `X-Service-Signature` headers.
  - ✅ **D5**: `ticket_service.py` — Scoped `reference_code` generation COUNT by `company_id` to prevent multi-tenant collisions.

---

### Phase 2: Architectural Stabilization ✅
- **Status**: Completed (2026-03-08)
- **Changes Applied**:
  - ✅ **Outbox Config**: `outbox_worker.py` — Migrated hardcoded `localhost:8008` URL to `common.config.settings` with Docker-network default fallback.
  - ✅ **DTO Enrichment**: `ticket_dto.py` — `TicketRead` now includes `history`, `resources`, `stop_logs`, and MES metrics (`module_origin`, `area`, `estimated_time`, `real_time_spent`, `cost_estimate`). Added `TicketResourceRead` and `StopLogRead` DTOs.
  - ✅ **Tenant Cleanup**: Removed redundant `company_id` from `TicketRead` (managed by JWT).
  - ✅ **Soft-Delete**: Added `DELETE /tickets/{id}` endpoint with `is_active=False` + status set to `CANCELED`.
  - ✅ **Audit**: `soft_delete_ticket` records `TicketHistory` entry and triggers `AuditService.log_action`.

---

### Phase 3: Kardex Integration ✅
- **Status**: Completed (2026-03-08)
- **Changes Applied**:
  - ✅ **Inventory Client**: Created `IInventoryClient` port and `HttpInventoryClient` adapter using `httpx` to trigger Kardex `OUT` transactions.
  - ✅ **CQRS Atomic Logic**: Modified `TicketCommandHandler.handle_consume_resources` to execute the HTTP dispatch *before* the local DB commit. Fast-fail uses `HTTPException` to safely abort the transaction upon external errors.
  - ✅ **Price Validation Metadata**: Added `warehouse_id` to `ConsumeResourceDto` ensuring `inventory_service` receives proper contextual data for accurate material costing.
  - ✅ **Endpoint Exposed**: Implemented `POST /tickets/{id}/consume-resources` returning standard `ApiResponse`.

---

## Missing Logic / Pending Backlog
- Automated tests for `create_internal_ticket_with_debouncing` (burst window mocking).
- HMAC signature verification with shared static secret.
- Background Consumer to process state updates originated from other services.
- GraphQL/REST endpoints for frontend dashboard (MTTR, MTBF, OEE).

