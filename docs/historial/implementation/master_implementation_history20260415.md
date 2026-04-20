# Master Implementation History - 2026-04-15

## Architectural Decisions & Refactoring (WMS / Flow)
- **High-Velocity Testing Architecture Bypasses**: Created and refined `scripts/simulate_liquor_distro.py`, a script explicitly created for local stress-testing and high-level structural integrity validation. This bypassed standard API calls for DB raw insertions via SQLAlchemy (`conn.execute("")`). Because of the decoupling, previous domain schema evolution (`inventory_transactions` vs `inventory_movements`, or missing attributes like `is_transit`) had to be synchronized manually inside the script raw arrays to conform.
- **Strict Role Boundaries (Authentication / Security)**: During data synthesis, validated that Cross-Service SSOT for identity is preserved. All user allocations to scopes happen purely inside `user_company_roles` bridging relationships correctly and safely mapping front-end visual routes (`*` admin, or operator limitations per branch).
- **No Pollution Standard Policy**: Validated that custom simulated scripts shouldn't be added to deployment loops or basic master operations (onboarding), storing corresponding disclaimers explicitly in `docs/scripts/` tree.
