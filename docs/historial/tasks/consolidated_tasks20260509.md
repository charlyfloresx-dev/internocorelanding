# Consolidated Tasks - 2026-05-09 (InternoCore POS)

## Backlog Superado (Completed)
- [x] **Hierarchical Pricing resolution ("Onion Layers")**:
    - [x] Backend implementation of price resolution order: Agreement > Warehouse > List > Public.
    - [x] Exposure of `partner_id` in `/lookup/{code}` endpoint.
    - [x] Integration of resolution logic in `inventory_service` checkout.
- [x] **Mobile POS B2B Integration**:
    - [x] Creation of `PartnerRepository` for customer lookups.
    - [x] Implementation of `PartnerSearchModal` for POS operator.
    - [x] State management in `ScannerBloc` to persist `selectedPartner`.
    - [x] Propagation of `partner_id` to product lookups and checkout.
- [x] **App Identity & Rebranding**:
    - [x] Renamed app to **INTERNO POS**.
    - [x] Updated Android `label` and Flutter `MaterialApp` title.
    - [x] Adjusted UI headers in `ScannerScreen`.
- [x] **Quality Assurance & Governance**:
    - [x] Developed `generate_mobile_graph.py` (Mobile Code Graph Auditor).
    - [x] Validated architecture compliance for Flutter (Clean Arch, Localization, Theme).
    - [x] Executed and validated 100% compliance in Backend Code Graph.

## Pendientes (Backlog)
- [ ] **Logistics Entry Flow**: Implement scanning for receiving documents (Entradas).
- [ ] **Inventory Audits**: "Price-less" counting flows.
- [ ] **Setup UX**: Warehouse selector in the terminal provisioning flow.
- [ ] **Notifications**: Real-time counter for pending receipts on the mobile dashboard.
- [ ] **Localization Debt**: Resolve 8 localization/theme warnings identified by `generate_mobile_graph.py`.

---
**Status:** 🚀 Phase 93 COMPLETED — B2B Pricing & Mobile Governance Active.
