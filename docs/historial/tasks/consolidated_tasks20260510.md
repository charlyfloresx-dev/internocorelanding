# Consolidated Tasks - 2026-05-10

## Completed Tasks ✅
- [x] **Backend Entitlements**: Seeded `inventory_core` module in `unified_industrial_seed.py`.
- [x] **Auth Service**: Implemented `/delegate-selection` for Zero-Trust mobile pairing.
- [x] **Security Guard**: Refactored `SubscriptionGuard` to allow `*` scope bypass.
- [x] **Frontend Web**: Updated `PosLinkDrawerComponent` with Selection Token QR.
- [x] **Mobile App**: Updated `LoginScreen` to handle `selectionToken` and auto-select company.
- [x] **Industrial UX**: Increased quantity input size for glove usage.
- [x] **Hardware Stability**: Physically remove `MobileScanner` widget during sheet transitions.
- [x] **Bug Fix**: Resolved `MX$` string interpolation error in Flutter.

## Pending Backlog 🔄
- [ ] **Mobile Bulk Checkout**: Validate performance with carts > 50 items.
- [ ] **Warehouse Discovery**: Dynamic mapping in the mobile selection flow.
- [ ] **Offline Resilience**: Design local SQLite buffer for offline scanning.
- [ ] **Audit Linkage**: Inject `terminal_id` in forensic logs.
