# Master Implementation History - 2026-05-09

## Phase 93: Hierarchical Pricing ("Onion Layers") & B2B Mobile POS

### 1. Architectural Strategy: The "Onion Layers" Engine
The goal was to eliminate price inconsistency during mobile transactions by enforcing a server-side hierarchical lookup.

**Order of Precedence:**
1.  **PriceAgreement (B2B):** Direct contract between `company_id` and `partner_id`.
2.  **ProductPrice (Warehouse):** Geo-specific pricing for the active `warehouse_id`.
3.  **ProductPrice (Assigned List):** Partner's `price_list_index` mapping (Level 1-10).
4.  **ProductPrice (Public):** Default list for anonymous/general public customers.

### 2. Technical Implementation Details

#### Backend (Master Data & Inventory)
- **`ProductService.lookup_product_by_code`**: Refactored to accept optional `partner_id`. If provided, it queries `PriceAgreement` first.
- **`inventory_service/pos_checkout`**: Added a validation step that re-triggers the "Onion Layers" resolution to verify that the price sent by the mobile app is authorized, preventing client-side price injection.

#### Mobile (Flutter - INTERNO POS)
- **Repository Pattern**: Extended `ProductRepository` to propagate `partner_id`.
- **Bloc Architecture**: `ScannerBloc` now acts as a state container for the `selectedPartner`. When a barcode is scanned, the bloc automatically inyects the `selectedPartner?.id` into the repository call.
- **UI/UX**: Created `PartnerSearchModal` using `SearchDelegate` patterns for high-speed customer lookup (filtering by `type=CUSTOMER`).

### 3. Governance: Mobile Code Graph Auditor
To maintain architectural parity with the backend, a new auditor was introduced:
- **Script**: `interno_billing_app/scripts/generate_mobile_graph.py`
- **Logic**: Uses regex-based AST analysis to detect:
    - **Hardcoded URLs** (Security).
    - **Clean Architecture Violations** (Separation of Concerns).
    - **Theme Compliance** (UI/UX Consistency).
    - **Localization Debt** (i18n Readiness).

### 4. Rebranding Strategy
The app was renamed from a generic "Billing App" to **INTERNO POS** to align with the industrial ERP positioning. This involved changes in:
- `android/app/src/main/AndroidManifest.xml` (`android:label`)
- `lib/main.dart` (`title`)
- `lib/features/scanner/presentation/scanner_screen.dart` (Header UI)

---
**Status:** ✅ Stabilized & Documented.
