# Consolidated Tasks - 2026-04-03

## 📦 Backend (Inventory Service)
- [x] Fix `external_reference` Not-Null / Unique constraint in model `InventoryDocument`.
- [x] Unblock Flow 3 SoD / Anti-Fraud blocks temporarily for internal tests.
- [x] Validate execution of `flow_1_entry.py`.
- [x] Validate execution of `flow_2_exit.py`.
- [x] Validate execution of `flow_3_internal_transfer.py`.
- [x] Validate execution of `flow_4_ict_enterprise_to_logistics.py`.
- [x] Validate execution of `flow_5_ict_binational.py` and Customs requirement validations.
- [x] Fix duplicate Reference error in `seed_ict_real.py` on mirrors.
- [x] Verify data exists inside `inventory_db` Docker Container.
- [x] Generate Code Graph and audit codebase structural invariants.
- [x] Sync documentation (`TESTS_AND_SCRIPTS_MAP.md`, `SERVICE_LOG.md`, etc.).

## 🖥️ Frontend (Angular & Tailwind)
- [x] Fix the redirect issue when switching companies in the Header (now preserves current route).
- [ ] Investigate and resolve the ESBuild error compiling `inventory-transfer.component.css`: `Cannot apply unknown utility class bg-surface-card`
- [x] Connect the UI Dashboard to correctly display the validated 11 rows of data stored inside `inventory_db`.

## ⚙️ Master Data & Auth (Dependencies)
- [x] Force instantiation of ghost-dependent Auth tables (`companies`) inside the `inventory_service` database domain.
- [ ] Configure `mes_service` integration for finalizing Pending Financial Valuations on binational transfers.
