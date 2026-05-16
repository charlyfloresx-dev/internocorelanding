# Master Implementation History - 2026-05-16

## Phase 108: Industrial Ecosystem Cold-Start & Seed Hardening

### Objective
Achieve a 100% reproducible development environment from a "nuclear" state, ensuring that all microservices initialize their schemas correctly and share a unified industrial dataset.

### Architectural Decisions
1. **Migration Baselines**:
   - Standardized on the `000_service_baseline.py` pattern across all microservices.
   - Consolidated HCM migrations to include `external_contacts`, resolving the "Triple Identity" gap in the industrial support flow.
2. **Deterministic Seeding**:
   - Utilized fixed UUIDs (SSOT) across all service seeds to enable cross-database relational integrity (e.g., `company_id` in `hcm_db` matching `id` in `dbname`).
3. **Subprocess Isolation**:
   - Shifted from direct Python imports in `unified_industrial_seed.py` to `subprocess.run` calls.
   - **Rationale**: SQLAlchemy creates a global engine/session factory upon import. In a multi-database seed environment, importing multiple services into a single process leads to "Session Pollution" where a service tries to query its tables in the wrong database.
4. **State Reset (Alembic)**:
   - Implemented manual TRUNCATE of `alembic_version` tables during baseline transitions to force re-application of schemas without requiring manual database dropping.

### Verification Results
- **Gateway**: `[ OK ]` (200 OK)
- **Auth Service**: `[ OK ]` (400 BadRequest - Expected from root ping)
- **HCM Service**: `[ OK ]` (Table `external_contacts` verified)
- **Unified Seed**: `SUCCESS` (Industrial dataset persisted)

### Summary of Infrastructure Changes
- **Updated**: `backend/scripts/unified_industrial_seed.py` (Subprocess logic).
- **Added**: `backend/hcm_service/alembic/versions/000_hcm_baseline.py`.
- **Cleaned**: Deleted fragmented HCM migrations.
