# CMMS Service - Engineering Log

This file acts as the Single Source of Truth (SSOT) for the technical decisions, architecture, and state of the `cmms_service`.

### [2026-05-04] Phase 1: CMMS Foundation & Clean Architecture
- **Objective**: Establish the core domain for Computerized Maintenance Management System (Assets & Maintenance).
- **Architecture**: Clean Architecture. Separated models into individual files (`asset.py`, `work_order.py`, etc.).
- **Shared Kernel**: Extracted `WorkOrderBase` to `common/models` to ensure compatibility with Production (MES) and Logistics (WMS). The CMMS implementation specifically uses `MaintenanceWorkOrder`.
- **Integrations**:
  - **Inventory**: Tools and Consumables operate as a metadata overlay on top of `inventory_service` via `inventory_item_id`.
  - **Storage**: Maintenance evidence uses `StorageService` with `StorageQuota` pre-flight validation.
- **Pending/Deltas**:
  - Implement `POST /work-orders/{wo_id}/consume` to register consumables definitively (Inventory `PICK_AND_CONSUME`).
  - Configure Domain Event dispatcher to notify Inventory Service of checkouts.
