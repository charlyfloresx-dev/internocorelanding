# InternoCore: Master Implementation History (2026-05-16)

---

## Phase 106: Industrial Auth & Menu Reconciliation ✅ COMPLETED

### Objective
Align the industrial authentication flow (RFID/PIN) with the administrative menu architecture to ensure warehouse operators have immediate and persistent access to inventory modules.

### Implementation Summary
- **JWT Scope Enrichment**: `collaborator_login_command.py` — injected `scopes` claim into JWT.
- **Smart Login (Frontend)**: Angular `LoginComponent` auto-detects industrial identifiers, redirecting to `collaboratorLogin` endpoint automatically.
- **Kiosk Validation**: `kiosk_auth_flow.py` upgraded with real-time JWT decoding and scope verification.
- **Migration Sweep**: `migrate_all.ps1` expanded to include `hcm-service`.
- **Idempotent Seed**: `_safe_add` helper refactored to `session.merge` (UPSERT pattern).

---

## Phase 107: Multi-DB Microservice Orchestration & Schema Stabilization

### Objective
Resolve cross-database seeding failures, stabilize the `inventory_db` schema, and establish a fully automated one-command environment bootstrap.

### Architectural Context

#### Current DB Topology (Microservices Mode)
| Container | Database | Tables Status |
|---|---|---|
| `interno-auth-dev` | `dbname` | ✅ 18 tables (full) |
| `interno-master-data-dev` | `master_data_db` | ✅ 19 tables + `translation_key` migration applied |
| `interno-inventory-dev` | `inventory_db` | ❌ 1 table only (`inter_company_transfers`) |
| `interno-tickets-dev` | `tickets_db` | ❌ 0 tables |
| `interno-hcm-dev` | `hcm_db` | ✅ 3 tables |
| `interno-subscription-dev` | `subscription_db` | ✅ 7 tables |

### Completed Work (Phase 107)

#### 1. Gateway CORS Fix
- **File**: `infrastructure/docker/nginx.conf`
- **Problem**: `add_header` directives inside `if` blocks caused `[emerg]` Nginx crash on startup.
- **Fix**: Moved all `add_header` CORS directives to the `server {}` block level. Global CORS now applies to all responses without conditional logic.

#### 2. Inventory StockRelocationCreate Schema
- **File**: `inventory_service/inventory_app/schemas/stock.py`
- **Problem**: `ImportError` on service boot — `inventory_app.services.inventory` imported `StockRelocationCreate` which didn't exist.
- **Fix**: Defined `StockRelocationCreate(BaseModel)` with `source_location_id`, `destination_location_id`, `quantity`, `notes` fields.

#### 3. Unified Seed: Multi-DB Architecture
- **File**: `backend/scripts/unified_industrial_seed.py`
- **Problem**: Original seed used a single `AsyncSessionLocal` connected to `dbname` (Auth DB), causing `UndefinedTableError` when seeding Master Data (`uoms` table), Inventory, etc.
- **Fix**: Introduced `get_session_factory(db_name)` helper that dynamically builds a session factory for each microservice database by parsing and replacing the DB name in the connection URL. Orchestrator now uses separate sessions per section:
  - Section 1: Auth (`dbname`)
  - Section 2: Subscriptions (`subscription_db`)
  - Section 3: Master Data (`master_data_db`)
  - Section 4: Inventory (`inventory_db`)
  - Section 5: Tickets (`tickets_db`) + HCM (`hcm_db`)

#### 4. Master Data: `translation_key` Migration
- **Service**: `master_data_service`
- **Problem**: Column `translation_key` existed in the SQLAlchemy `MovementConcept` model but was never added via migration. The `58e0de261a29` migration that recreated `movement_concepts` omitted it.
- **Fix**: Generated `f21020a05ace_add_translation_key_to_movement_concepts.py` via `alembic revision --autogenerate` inside container. Applied via `alembic upgrade head`. ✅

#### 5. Dead Code Removal
- **Deleted**: `backend/scripts/create_all_tables.py` — was a monolith-era artifact that used a shared `Base.metadata.create_all`, conflicting with per-service migration strategy.

### Root Cause Analysis: Inventory DB Failure

The `inventory_db` migration chain is broken from a fresh state:

```
None → 42ea522fc124 (initial_schema_from_existing)
       ↓ tries to drop columns from inventory_movements — TABLE DOESN'T EXIST
       ↓ → PostgreSQL aborts transaction
       ↓ → Alembic can't insert version row → InFailedSQLTransactionError
       ↓ → exit code 1, inventory_db stays empty
```

The migration `42ea522fc124` was originally generated against a pre-existing database that already had the inventory tables from the monolith era. In a clean `inventory_db`, those tables do not exist, so the `_safe_drop_column('inventory_movements', ...)` call generates a SQL error that aborts the entire transaction.

**Downstream impact**: `86a6ad039d59_audit_hardening` also assumes these tables exist and adds `tenant_id` columns to them. The entire migration chain is incompatible with a fresh database.

### Implementation Plan: Phase 107 Completion

#### Step 1 — Fix `inventory_service` Migration Chain (P0 BLOCKER)
**Action**: Create `000_inventory_baseline.py` as a new first migration that creates all core inventory tables using `IF NOT EXISTS` guards:
- `inventory_warehouses`, `inventory_locations`, `inventory_movements`, `inventory_stocks`, `inventory_item_variants`, `inventory_documents`, `inventory_transactions`, `inventory_boms`, `inventory_backflush_errors`, `inventory_levels`, `inventory_movement_concepts`, `stock_lots`, `idempotency_keys`, `file_metadata`

**Then**: Patch `42ea522fc124` to set `down_revision = '000_inventory_baseline'` and remove the unsafe `_safe_drop_column` calls (they're already handled later). Patch `86a6ad039d59` to wrap all `ALTER` operations in try/except since those tables will now exist from baseline.

**Expected result**: `docker exec interno-inventory-dev alembic upgrade head` exits 0.

#### Step 2 — Update `migrate_all.ps1` (P0)
Add missing containers to sweep:
```powershell
"interno-tickets-dev",
"interno-subscription-dev",
"interno-notification-dev"
```

#### Step 3 — Fix `inventory_service/scripts/seed.py` Auto-Detect (P1)
Remove the mandatory `--company-id` CLI argument. Replace with:
```python
company = (await session.execute(select(Company).limit(1))).scalar_one_or_none()
COMPANY_ID = company.id if company else ENTERPRISE_ID_FALLBACK
```
This allows `entrypoint.sh` to call `python scripts/seed.py` without human input.

#### Step 4 — Validate Seed End-to-End (P1)
Once Steps 1-3 are complete, re-run:
```
python backend/scripts/unified_industrial_seed.py
```
Expected: All 7 sections succeed with `DONE (Merged)` logs.

#### Step 5 — Nginx Startup Order Fix (P2)
Add `depends_on` with `service_healthy` for all service containers in `docker-compose.dev.yml` to prevent `host not found` upstream warnings:
```yaml
depends_on:
  interno-auth-dev:
    condition: service_healthy
```
Or use Nginx dynamic resolver with `resolver 127.0.0.11 valid=30s;` and `set $upstream ...` pattern to make Nginx tolerant of temporarily missing upstreams.

### Technical Decisions

1. **Per-service DB session over shared session**: Each microservice owns its database. The seed script now respects this boundary. Cross-DB data (e.g., Company IDs) is replicated via constants (SSOT UUIDs), not by ORM joins.

2. **Baseline Migration over autogenerate patching**: Creating a `000_baseline` is safer than patching individual migrations with try/except scattered throughout. It establishes a clean contract: "from zero, run this to get full schema".

3. **Idempotent seeds over re-seeding**: The `_safe_add` + `session.merge` pattern ensures seeds can be re-run on existing data without errors, critical for development workflow.

### Environment Status (End of Session)
| Component | Status | Notes |
|---|---|---|
| `interno-gateway-dev` | ✅ Running | CORS headers fixed, config test passes |
| `interno-auth-dev` | ✅ Running | Full schema, seed ready |
| `interno-master-data-dev` | ✅ Running | `translation_key` migration applied |
| `interno-inventory-dev` | ⚠️ Running (degraded) | Service starts, but DB schema is incomplete |
| `interno-tickets-dev` | ⚠️ Running (degraded) | `tickets_db` is empty |
| `interno-hcm-dev` | ✅ Running | Schema OK |
| `interno-subscription-dev` | ✅ Running | Schema OK |
| `unified_industrial_seed.py` | 🔴 Blocked | Fails at Section 4 (inventory_db incomplete) |
