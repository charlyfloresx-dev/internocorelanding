# Consolidated Tasks - 2026-04-01

## ✅ Completed (Sprint / Session)
- **Backend Infrastructure Optimization**:
  - Implemented `Base.metadata.create_all()` across Inventory Schema for true Idempotent bootings.
  - Added safety checks (`_table_exists()`, `type_exists()`) inside `master_data_service` Alembic revisions to decouple domains during bootstrap.
  - Conducted full teardown (`docker compose down -v`) and recovery tests natively verifying Postgres initialization.
- **Data & Seed Layer**:
  - `test_full_ict_cycle.py` executed successfully simulating Binational Transfers correctly against Ghost Stock schemas.
  - `master_seed.py` completed flawlessly ensuring baseline configuration for `companies`, `uoms`, `warehouses` over empty databases.
- **Frontend Core Stabilization**:
  - ESBuild runtime restored.
  - Angular computed `filteredOriginCompanies` and `filteredDestWarehouses` reactivated eliminating `500` request cascades entirely.

---

## ⏳ Pending / Next Up (Phase 42)
### Financial Clearing & Anexo 24 Dashboard
- **Backend: Pricing & Debt Recovery**
    - [ ] Create `GET /transfers/financial/pending` endpoint.
    - [ ] Create `POST /transfers/financial/clear/{transfer_id}` endpoint.
    - [ ] Add `FinancialDebtClearedEvent` to domain events.
- **Backend: Customs Intelligence**
    - [ ] Implement `get_customs_balances` in `SQLAlchemyInventoryRepository`.
    - [ ] Create `GET /customs/pedimento-aging` endpoint with IMMEX safety rules.
- **Frontend: Financial Clearing Widget**
    - [ ] Create `financial-clearing.component.ts`.
    - [ ] Implement bulk-selection for price regularization.
    - [ ] Add "Settle Price" modal with industrial validation.
- **Frontend: Anexo 24 Dashboard**
    - [ ] Create `compliance-dashboard.component.ts`.
    - [ ] Implement "Traffic Light" aging chart (Stay Time).
    - [ ] Add "Saldos por Pedimento" drill-down table.
- **Technical Debt & Governance**
    - [ ] Fix 54 Invariances found by `generate_code_graph.py` inside `backend/` domain (primarily MISSING idempotencies in handlers).
