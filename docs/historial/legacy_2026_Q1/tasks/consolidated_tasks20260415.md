# Consolidated Tasks - 2026-04-15

## Domain: Inventory Flow & Integration
- ✅ **Fix Inventory Script Constraints**: Resolved schema alignment issues in `inventory_warehouses`, including tracking of boolean missing constants (`is_transit`, `country_code`) inside the `simulate_liquor_distro.py` bypass.
- ✅ **Schema Unification Audit**: Discovered that `inventory_movements` table model transitioned to `inventory_transactions` in previous PR, thus the DB uses columns like `unit_price` instead of `unit_cost`. Reprogrammed the raw SQLAlchemy inserts properly to be able to bypass business API for stress-testing.
- ✅ **RBAC Massive Seed Injection**: Inserted raw User roles `tony@interno.com` (All access), `garry@interno.com` (Logistics only), and `tropy@interno.com` (Operator access) bridging their constraints directly in `user_company_roles` schema over `auth_db`.
- ✅ **Data Generation**: Populated the system with ~60 Master product variations across 4 simulated logistics nodes, inserting +180 inventory transactions directly in seconds.

## Upcoming / Pending
- ⬜ Validate the generated transaction logs through the Frontend Angular Interface (Forensic audits).
- ⬜ AWS Cloud Deploy (Frontend via CloudFront/S3, Backend API containers logic matching local tests).
