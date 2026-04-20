# Consolidated Tasks: 2026-04-13
## Phase 44: Industrial Pricing & Agreements

### 💎 Pricing & Commercial (Master Data)
- [x] **Inmutable Model**: Implement `PriceAgreement` with valid/until versioning.
- [x] **Reserved Level 0**: Configure all schemas and logic to use Level 0 as "COMPRA/COSTO".
- [x] **Dynamic Templating**: Add backend endpoints for pre-filled CSVs based on tenant inventory.
- [x] **Transactional Import**: Implement `POST /import` with Soft-Close + Insert logic.
- [x] **Import Dashboard (UI)**: Create `PriceImportDashboard` in Angular with Drag & Drop.
- [x] **Catalog Integration**: Button in header with automatic after-close refresh.

### 🏛️ Core Architecture & Infrastructure
- [x] **Alembic Inmutable**: Create and apply migration for `price_agreements`.
- [x] **Standardization**: Finish `CORE_` prefix migration (verified in previous session, confirmed today during model creation).
- [x] **UI Stabilization**: Modal full-screen (95vw/vh) for high-density price management.

### 🚧 Works in Progress (Phase 44.5)
- [ ] **Dashboard de Márgenes**: Comparative view level 0 vs levels 1-10.
- [ ] **Point-in-Time Query Service**: Engine utility to get the correct price for any historical date.
- [ ] **B2B Contract Document Upload**: Linking `document_reference` to S3 buckets.

### 📅 Backlog Industrial
- [ ] **Inventory Handshake**: Integration test for sales using the new pricing engine versioning.
- [ ] **AWS ECR Sync**: Pushing Master Data Service v2.1 to repository.
- [ ] **Forensic Logs Enhancement**: Propagate `source='CSV_IMPORT'` to the global `AuditLog`.

---
**SSOT - Last Updated:** 2026-04-13 12:10 PST
