# 📝 SERVICE LOG: Inventory Service

## [2026-03-15] - Dashboard Stabilization & High-Fidelity Data
- **Problem:** Mission Control Dashboard showed empty graphs and inconsistent valuation data due to timezone "naive" vs "aware" mismatches in Python.
- **Solution:** 
  - Standardized all datetime operations to **UTC-Aware** in `dashboard_handler.py`.
  - Refactored `seed.py` to use `datetime.now(timezone.utc)`.
- **New Feature: High-Fidelity Seeding:**
  - Automated generation of warehouse-specific status (Red/Yellow/Green) to match design template contrast.
  - Injected 250+ movements across 24h to ensure chart density.
  - Synchronized SKU names with Master Data Service for professional UI presentation.
- **Architecture:** 
  - Validated `X-Trace-ID` propagation from API to Repository.
  - Enforced strictly one `company_id` isolation per dashboard request.

## [2026-03-13] - Forensic Report Engine
- **Feature:** Implemented Kardex, WAC Valuation, and ABC Rotation reports.
- **Infrastructure:** Integrated SQL Window functions for deterministic balance calculations.
- **Security:** Zero-trust warehouse ownership validation implemented in repository base.
