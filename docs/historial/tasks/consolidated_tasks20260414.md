# Consolidated Tasks - 2026-04-14

## Master Data & Pricing (Industrial Core)

### ✅ Completed
- [x] **Fix `ProductPrice` Object Initialization**: Refactored to use `Money` value object effectively.
- [x] **Resolve `tenant_id` Constraint**: Explicitly injected `tenant_id` (company context) in all price/agreement creators.
- [x] **ORM Attribute Mapping**: Added `@property` for `amount` and `currency` in `ProductPrice` model to satisfy SQLAlchemy flush events.
- [x] **Soft-Close Validation**: Verified that importing a CSV correctly seals old prices via `valid_until` timestamp.
- [x] **B2B Agreement Stabilization**: Confirmed that `PriceAgreement` records are immutable and versioned.
- [x] **CSV Template Generation**: Created `docs/plantilla_carga_precios_industrial.csv` for standardized uploads.
- [x] **Mass Import Integration Test**: Successfully processed 18+ records from the industrial pricing matrix.

### 🟡 In-Progress
- [ ] **Frontend Validation Refinement**: Polish UI tooltips for price list descriptions.
- [ ] **Audit Log Verification**: Cross-referencing `audit_log` entries for price changes.

### 🔴 Pending
- [ ] **Cross-Border Transfer Pricing**: Implement transfer price logic (Price List 4) between MX and US entities.
- [ ] **UI Bulk Actions**: Enable one-click activation/deactivation of versioned price lists.
