# Master Implementation History — 2026-04-01

## Session Summary: Binational Inventory Schema & Startup Synchronization
Today's deep dive addressed a critical race condition between microservices initializing their databases. Specifically, both `inventory_service` and `master_data_service` crashed due to missing cross-domain dependencies (`warehouses`, `movement_concepts`, `movementtype`) when attempting to generate schemas concurrently from a clean PostgreSQL instance. 

We stabilized the multi-container environment by introducing defensive initialization patterns to Alembic and transitioning `inventory_service` towards a preemptive `Base.metadata.create_all()` bootstrapping strategy. Finally, we repaired the Angular frontend signals rendering the Binational Inventory Transfer HUD and succeeded in running our first end-to-end Binational Ghost Stock test.

---

### Technical Decisions & Architectural Patterns
1.  **Idempotent Schema Generation (Inventory Service):** 
    We shifted the `inventory_service` startup loop to execute `Base.metadata.create_all()` before continuing with Alembic migrations. This guarantees that tables are defined immediately based on current ORM domain models, bypassing Alembic failures triggered by "empty DB" conditions when Docker containers first spin up.
2.  **Cross-Domain Alembic Defense (Master Data Service):**
    Historical Alembic migrations in `master_data_service` attempted to `ALTER TABLE` structures (like `warehouses` or enum `movementtype`) that correctly belong to the `inventory_service` domain. To resolve this without manual seeding ordering, we implemented `_table_exists()` and `type_exists()` safety guards directly into Alembic `upgrade()` steps in `/master_data_service/alembic/versions`. This allows migrations to gracefully ignore missing tables until the authoritative service has spun up and built them.
3.  **Frontend Signals Restoration:**
    Angular compilation errors (`TS2339`) regarding `filteredOriginCompanies` and `filteredDestWarehouses` inside `inventory-transfer.component.ts` were debugged and fixed by returning missing signal bindings previously removed during the "Expedición Islandia" HUD update.

---

### Key Blockers Resolved
-   `UndefinedTableError`: Crashing `test_full_ict_cycle.py` on `customs_pedimento` because previous schemas were not purged, keeping invalid columns active. Addressed via `docker compose down -v` and a full reset.
-   `500 Internal Server Errors`: Frontend endpoints crashing as `master_data_service` failed to supply brand/uom tables recursively dragged down by Alembic failures.

---

### Rule Established (Environment Runbooks)
*   **Startup Tolerance:** We established that we won't strictly "force" wait conditions for migrations via docker compose scripts, but instead adopt *Idempotency* within the python code (`migrate_schema.py` and `alembic` modifications). The services must be capable of spinning up concurrently and skipping missing dependencies seamlessly.
*   **Seeding Flow:** `scripts/master_seed.py` should only be called *after* all microservices report a `200 OK` on their `/health` endpoints to ensure schemas are definitively written into the containerized postgres.

---

### Next Immediate Goals (Phase 42)
*   Deploy **Anexo 24 / Financial Clearing** architecture inside `inventory_service`.
*   Address the 54 invariances found by `generate_code_graph.py` (mainly idempotency missing inside handler scripts).
*   Extend the QA pipeline to incorporate Cloud/AWS deployment strategies.
