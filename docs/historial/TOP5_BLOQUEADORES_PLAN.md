# 📋 IMPLEMENTATION PLAN — Weeks 1-3: TOP5 Blockers Roadmap

**Date:** 2026-06-03  
**Status:** Ready for Approval  
**Scope:** 5 critical blockers preventing parallel development paths

---

## 📌 EXECUTIVE SUMMARY

After validating RTR Phase D (✅ COMPLETE), this plan lays out the sequential implementation of 4 remaining critical blockers blocking cloud deployment, mobile sales, and HR workflows.

**Key Finding:** POS Checkout E2E is blocked by a **missing `/inventory/warehouses` LIST endpoint** (quick fix, <1h). All other blockers have significant implementation work.

---

## 🎯 BLOCKERS TIMELINE

```
COMPLETED ✅         WEEK 1           WEEK 2-3        WEEK 4+
───────────────     ──────────────    ────────────    ────────
RTR Phase D ✅      POS Checkout E2E  HCM Phase 3 MVP  (Future)
(1h done)           (3h total)        (11h total)
                    ├─ GET /ware...   ├─ PermissionDoc
                    │  (+1h)          │ KardexEvent
                    ├─ Flow script    │ (+10h)
                    │  (+2h)          └─ Service layer
                    └─ Tests          
                                      PARALLEL:
Shift-End Auto-     Headcount         Shift-End
Logout pending      Recompute pending Auto-Logout
(3h)                (2.5h)            (3h)
```

---

## 🔴 BLOCKER #1: POS Checkout E2E Validation (3h) — QUICK WIN

### Current State
- ✅ Flow script exists: `backend/inventory_service/scripts/flows/flow_pos_checkout.py`
- ❌ **BLOCKED:** Endpoint `GET /inventory/warehouses` (list) does NOT exist
- ✅ All other endpoints exist: `/products/lookup`, `/inventory/levels`, `/pos/checkout`

### What's Missing
**Missing Endpoint:** `GET /api/v1/inventory/warehouses` (list all warehouses for company)
- **Location:** `backend/inventory_service/inventory_app/api/v1/endpoints/inventory.py`
- **Warehouse Model:** Already exists at `backend/inventory_service/inventory_app/models/warehouse.py`
- **Query Params:** `?warehouse_code=WH-001` (optional filter)
- **Response:** `{"data": [{"id": "...", "code": "WH-001", "name": "Main Warehouse", "type": "STANDARD", ...}]}`

### Implementation Plan
1. **Add GET /warehouses endpoint** (20 min)
   - Query `Warehouse` table filtered by `company_id` from JWT
   - Return `WarehouseRead` schema (id, code, name, type, location)
   - Use existing pattern from `inventory.py` (`@router.get(...)`)

2. **Execute flow_pos_checkout.py** (30 min)
   - Verify warehouse lookup passes
   - Verify stock check passes
   - Verify checkout creates InventoryDocument + movements
   - Verify stock decreases correctly

3. **Document results** (10 min)
   - Update consolidated_tasks20260604.md
   - Update inventory_service SERVICE_LOG.md

### Files to Modify
- `backend/inventory_service/inventory_app/api/v1/endpoints/inventory.py` — Add GET /warehouses
- `backend/inventory_service/inventory_app/schemas/inventory.py` — Add WarehouseRead (if missing)

### Success Criteria
- [ ] GET /inventory/warehouses returns 200 with warehouse list
- [ ] flow_pos_checkout.py executes without errors
- [ ] All 7 flow steps pass: Auth → Warehouse → Stock → Price → Checkout → Verify

---

## 🔴 BLOCKER #2: Shift-End Auto-Logout (3h) — APScheduler Job

### Current State
- ✅ `LaborDensityService.materialize_range()` exists and works
- ✅ `ProductionRun`, `Shift` models exist with `start_time`, `end_time`, `is_overnight`
- ✅ Labor clock-in/out endpoints exist
- ❌ **MISSING:** Automated shift-end trigger + auto clock-out logic

### What's Missing
A scheduled background job that runs every minute and:
1. Finds all active ProductionRun records where `shift.end_time <= NOW()`
2. For each: calls `LaborDensityService.materialize_range(shift.start_time, shift.end_time)`
3. Emits `ShiftEnded` event for audit
4. Does NOT block if materialize fails (best-effort)

### Implementation Plan
1. **Create `mes_app/scheduler.py`** with APScheduler (60 min)
   - `@app.lifespan` context manager to start/stop scheduler
   - Job: `check_shift_end_and_close_labor()` runs every 60 seconds
   - Query ProductionRun where `shift.end_time <= datetime.now(timezone.utc)`
   - Call `LaborDensityService.materialize_range()` for each
   - Emit `ShiftEnded` domain event
   - Log with production_run_id, labor_id, timestamp

2. **Integrate into main.py** (30 min)
   - Create scheduler in `app.lifespan` (async context manager)
   - Set grace_period = 15 minutes (allow overtime without blocking)

3. **Write tests** (30 min)
   - 8+ tests: shift detection, edge cases (midnight), concurrency guard

### Files to Create/Modify
- `backend/mes_service/mes_app/scheduler.py` — NEW (APScheduler job definition)
- `backend/mes_service/mes_app/main.py` — Integrate scheduler in lifespan
- `backend/mes_service/mes_app/services/labor_density_service.py` — Extend with event emission

### Success Criteria
- [ ] APScheduler job runs every 60s
- [ ] Job detects shift end correctly
- [ ] LaborDensityService.materialize_range() called with correct time range
- [ ] ShiftEnded event emitted
- [ ] Tests pass (8+)

---

## 🔴 BLOCKER #3: Headcount Recompute Integration (2.5h) — Event Chain

### Current State
- ✅ `HourlyLaborSnapshot` model exists with headcount fields
- ✅ MES reads from HourlyLaborSnapshot via `/headcount/{resource_id}` endpoints
- ❌ **MISSING:** HCM → MES event chain (PermissionDocumentPosted → headcount recompute)

### What's Missing
Three-part event chain:
1. **PermissionDocumentPosted event schema** (hcm_service)
2. **Outbox pattern** in hcm_service to publish event
3. **MES consumer** to listen and recompute headcount

### Implementation Plan
1. **HCM: Define PermissionDocumentPosted event schema** (30 min)
   - File: `backend/hcm_service/hcm_app/domain/events/permission_events.py`
   - Schema: `company_id`, `document_id`, `collaborator_id`, `permission_type`, `start_date`, `end_date`, `is_posted_at`
   - Emit in `PermissionService.approve_and_post_by_rh()`

2. **HCM: Outbox pattern (if not exists)** (40 min)
   - Check if `hcm_app/services/outbox_event_publisher.py` exists
   - If not: Create outbox table + publisher that publishes to Notification Service
   - Use existing pattern from `inventory_service/outbox_event_publisher.py`

3. **MES: Create headcount recompute consumer** (40 min)
   - File: `backend/mes_service/mes_app/services/headcount_recompute_service.py`
   - Logic: `on_permission_document_posted()` 
     - Recomputes `HourlyLaborSnapshot` for affected dates
     - Uses `LaborDensityService.materialize_range(permission.start_date, permission.end_date)`
     - Logs result (best-effort, does NOT block)

4. **Tests** (20 min)
   - Mock PermissionDocumentPosted event
   - Verify headcount recomputation logic
   - Test fallback (old headcount used if recompute fails)

### Files to Create/Modify
- `backend/hcm_service/hcm_app/domain/events/permission_events.py` — NEW event schema
- `backend/hcm_service/hcm_app/services/outbox_event_publisher.py` — NEW or existing outbox
- `backend/mes_service/mes_app/services/headcount_recompute_service.py` — NEW consumer

### Success Criteria
- [ ] PermissionDocumentPosted event emitted after posting
- [ ] Event published to Notification Service
- [ ] MES consumer receives event and recomputes headcount
- [ ] Tests pass (10+)

---

## 🟠 BLOCKER #4: HCM Phase 3 MVP (11h) — Kardex Transactional

### Current State
- ❌ **MISSING:** PermissionDocument model (design exists in README, not in code)
- ❌ **MISSING:** KardexEvent model (design exists in README, not in code)
- ⚠️ **PARTIAL:** EligibilityService (logic in endpoint, needs service layer)
- ✅ **Endpoint EXISTS:** GET /collaborators/{id}/eligibility (already functional)

### What's Missing
The full Kardex system:
1. **PermissionDocument header** (states: DRAFT → PENDING_SUPERVISOR → PENDING_RH → POSTED)
2. **PermissionMovement detail lines** (dates, types, salary impact)
3. **KardexEvent append-only log** (immutable audit of all changes)
4. **EligibilityService** (domain service layer for validation)
5. **Permission endpoints** (CRUD + state transitions)
6. **Kardex audit endpoint** (GET /collaborators/{id}/kardex)

### Implementation Plan (11 hours, 6-9 PRs)

**PR-HCM-005: PermissionDocument Model + Service** (3h)
- Create `hcm_app/models/permission_document.py`
  - States: DRAFT, PENDING_SUPERVISOR, PENDING_RH, POSTED
  - Fields: id, company_id, collaborator_id, document_type, status, supervisor_id, supervisor_signed_at, hr_approver_id, hr_posted_at, created_at, audit_notes
  - Timestamps with `datetime.now(timezone.utc)` (Phase 177 pattern)
  - Inherits from `MultiTenantBase`

- Create `hcm_app/services/permission_service.py`
  - `create_permission_request()` → DRAFT
  - `approve_by_supervisor()` → PENDING_RH
  - `approve_and_post_by_rh()` → POSTED + emit PermissionDocumentPosted
  - Uses `begin_nested()` for atomicity
  
- Create endpoints: POST, GET, PATCH /permissions

**PR-HCM-006: PermissionMovement Model** (2h)
- Create `hcm_app/models/permission_movement.py`
  - Fields: id, document_id, start_date, end_date, movement_type, quantity_days, salary_impact (Money), is_salaried
  - Header-detail relationship to PermissionDocument

**PR-HCM-007: KardexEvent Model** (1.5h)
- Create `hcm_app/models/kardex_event.py` (append-only, no updates/deletes)
  - Fields: id, company_id, collaborator_id, event_type, document_id, affects_eligibility, eligibility_penalty_until, description, created_at
  - Event listeners SQLAlchemy block UPDATE/DELETE

**PR-HCM-008: EligibilityService** (2h)
- Refactor logic from `api/v1/endpoints/collaborators.py` into `hcm_app/services/eligibility_service.py`
  - `is_eligible_for_promotion(collaborator_id: UUID, company_id: UUID) -> bool`
  - Logic: Query KardexEvent where `affects_eligibility=True` in last 90 days
  - If any found → not eligible
  - Tests: 15+ (happy path, edge cases, 90d boundary)

**PR-HCM-009: GET /internal/check-eligibility endpoint** (1h)
- **ENDPOINT ALREADY EXISTS** at `GET /collaborators/{id}/eligibility`
- Alias or forward: `GET /internal/check-eligibility/{collaborator_id}?company_id={id}`
- Returns: `{"eligible": bool, "penalty_until": datetime, "reason": str}`

**PR-HCM-010: Kardex Audit Endpoint** (1.5h)
- `GET /collaborators/{id}/kardex?from_date={date}&to_date={date}`
- Returns paginated list of KardexEvent
- Paging: 50 items per page

### Files to Create
- `backend/hcm_service/hcm_app/models/permission_document.py`
- `backend/hcm_service/hcm_app/models/permission_movement.py`
- `backend/hcm_service/hcm_app/models/kardex_event.py`
- `backend/hcm_service/hcm_app/services/permission_service.py`
- `backend/hcm_service/hcm_app/services/eligibility_service.py`
- `backend/hcm_service/alembic/versions/<hash>_add_permission_document.py` (migration)
- `backend/hcm_service/alembic/versions/<hash>_add_kardex_event.py` (migration)

### Success Criteria
- [ ] PermissionDocument model + CRUD endpoints
- [ ] KardexEvent append-only model
- [ ] EligibilityService validates 90-day rule
- [ ] GET /internal/check-eligibility returns correct eligibility
- [ ] 50+ tests pass (across all PRs)
- [ ] Code graph: 0 CRITICAL
- [ ] SERVICE_LOG.md updated

---

## 📊 EXECUTION ROADMAP

### Week 1 (This Week)
- **DONE ✅** RTR Phase D validation (1h, 2026-06-03)
- **TODO** POS Checkout E2E (3h, start 2026-06-04)
  - Implement GET /warehouses (1h)
  - Run flow_pos_checkout.py (2h validation)
- **PARALLEL** Start Shift-End Auto-Logout design (design phase, no code)
- **PARALLEL** Start Headcount Recompute design (design phase, no code)

### Week 2-3 (June 9-20)
- **Shift-End Auto-Logout** implementation (3h) — APScheduler job
- **Headcount Recompute** implementation (2.5h) — event chain
- **HCM Phase 3 MVP** kickoff (11h) — PermissionDocument + KardexEvent + services

### Week 4+ (June 23+)
- Mobile E2E testing
- Cloud deployment
- Infrastructure hardening

---

## ✅ VERIFICATION STRATEGY

### POS Checkout
- [ ] Run `flow_pos_checkout.py` → all 7 steps PASS
- [ ] Stock decreases by 1 unit

### Shift-End Auto-Logout
- [ ] APScheduler detects shift end
- [ ] LaborDensityService.materialize_range() called
- [ ] Tests: 8+

### Headcount Recompute
- [ ] PermissionDocumentPosted event fires after POSTED
- [ ] MES consumer receives and recomputes
- [ ] Tests: 10+ (including fallback scenarios)

### HCM Phase 3 MVP
- [ ] PermissionDocument state machine: DRAFT → PENDING_RH → POSTED
- [ ] KardexEvent immutable (no UPDATE/DELETE possible)
- [ ] EligibilityService: 90-day rule enforced
- [ ] GET /internal/check-eligibility returns correct eligibility
- [ ] Tests: 50+ across all 6 PRs

---

## 🚀 NEXT STEPS

1. **Approve this plan** 
2. **Week 1:** Implement POS Checkout E2E (3h)
3. **Week 2-3:** Implement remaining blockers (16.5h)
4. **Week 4+:** Cloud deployment readiness

---

**Status:** Ready for Approval  
**Generated:** 2026-06-03  
**Responsible:** Tech Lead (Carlos Flores)
