# Master Implementation History — 2026-04-10

## Session Overview
**Date:** 2026-04-10  
**Focus:** Catalog Lifecycle Governance + Product Wizard (Alta Rápida)

---

## Phase 33.4 — Administrative Governance (RBAC) Completion

### Backend (master_data_service)
**Files modified:**
- `app/api/v1/endpoints/categories.py` — Added role guard (`admin/owner/superadmin`) on POST, PATCH, DELETE
- `app/api/v1/endpoints/brands.py` — Same RBAC enforcement
- `app/api/v1/endpoints/uom_router.py` — RBAC guards on write operations
- `app/schemas/product.py` — Extended `ProductCreate` with fiscal and physical tracking fields:
  - `brand_id`, `requires_batch`, `requires_expiration`
  - `sat_product_code` (max 20), `hts_code` (max 20)
  - `is_taxable` (bool, default True), `allow_price_override` (bool, default True)

### Frontend Shared Modals (all standalone components)
**Guard-First pattern implemented across:**
- `partner-modal.component.ts` — AuthService integrated, form disable on non-admin + soft-delete button
- `concept-modal.component.ts` — RBAC + delete
- `category-brand-modal.component.ts` — RBAC + delete
- `uom-modal.component.ts` — RBAC + delete (delete button only visible to admin, save button disabled for non-admin in edit mode)

**Pattern standardized:**
```typescript
const roles = this.auth.roles();
this.isAdmin.set(roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin'));
if (!this.isAdmin()) this.form.disable();
```

---

## Phase 33.5 — Prices & Fiscal Catalogs

### Backend
**Models added/modified:**
- `app/models/product_price.py` — ProductPrice with `valid_until` (soft-close), `is_manual` (audit flag), `price_list_index` (1–10), `currency`, `unit_type (BASE/SALE)`
- Alembic migration `cc4ea7bf91a2_add_price_soft_close_and_manual_flag.py` applied
- Migration chain: `bb3da9fcddfd → e5703c10603a → cc4ea7bf91a2`

**Service Layer:**
- `MasterDataService` — Added `createProduct`, `updateProduct`, `deleteProduct`, `getPrices`, `upsertPrice`, `deleteUom` methods

### Frontend Service Interface Enhancements
- `master-data.service.ts` — Added interfaces: `ProductPrice` (with `valid_until`, `is_manual`, `warehouse_id`)
- `Partner` interface — Added `email?: string`
- `Product` interface — Added `sat_product_code?`, `hts_code?`, `is_taxable`, `allow_price_override`, `last_price`, `currency`

---

## Phase 33.6 — Product Creation Wizard (Alta Rápida)

### Architecture Decision: Excel-Style Fast Entry
**Rejected:** Multi-step wizard (too bureaucratic for high-volume entry)  
**Adopted:** Full-screen grid-based entry (like Excel), multiple rows simultaneously

**Component:** `frontend/src/app/modules/catalog/product-wizard.component.ts`

**Design specs:**
- Full-screen overlay, no pagination or step chrome
- Each row = one product in progress
- Columns: `#` · `SKU*` · `Nombre*` · `Tipo` · `UOM*` · `Precio` · `Categoría` · `Cód. SAT`
- Keyboard: `Tab` = next field, `Enter` = new row, `Esc` = close
- Per-row save OR bulk "Guardar Todo"
- Error recovery: retry per-row without losing others
- Price field is OPTIONAL — saves product without price, adds to "incomplete" panel

**Minimum required fields to save:** SKU + Name + UOM  
**Optional:** Price (Tier 1), Category, SAT Code

### Incomplete Products Dashboard Panel
**Component:** `product-catalog.component.ts` — Added above the main table

Features:
- `computed` signal: `incompleteProducts()` — filters products missing price, SAT code, or category
- Collapsible amber alert panel with per-product missing-field pills
- "Filtrar" toggle to show only incomplete products in the main table
- Direct "Precios" action button per incomplete row → opens `ProductPriceListComponent`
- Global products (company_id = null) excluded from completeness check

---

## Architectural Patterns Established This Session

| Pattern | Where Used |
|---|---|
| Guard-First UI | All catalog modals |
| Polymorphic Modal (Create/Edit) | All catalog modals |
| Immutable Price (Soft-Close) | ProductPrice model via `valid_until` |
| Excel-Style Bulk Entry | ProductWizardComponent |
| Incomplete Completeness Tracking | ProductCatalogComponent computed signal |

---

## Blockers & Resolutions

| Blocker | Resolution |
|---|---|
| `TS2339: email does not exist on Partner` | `email?: string` added to `Partner` interface in `master-data.service.ts`. Build was caching old version — resolved on next successful build (`17:41:55`) |
| `TS2349: expression not callable` (old wizard) | Caused by step-based form union type. Resolved by replacing with row-based `FormsModule` (ngModel) — no FormGroup union ambiguity |
| `ForeignKeyConstraint` on product_prices→warehouses | Removed DB-level FK (cross-microservice boundary). Reference kept as logical UUID without constraint |
| Seed script crashing on empty DB | Moved `create_all()` before TRUNCATE; wrapped in try/except for clean environments |
