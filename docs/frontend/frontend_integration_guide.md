# Frontend Integration Guide: InternoCore Backend Updates

This guide outlines the critical changes in the backend microservices (Auth, Inventory, Master Data) and how the Angular frontend should adapt to them.

## 1. Auth Service: RBAC & Multi-tenancy
The login flow now follows a **Two-Phase Handshake**.

### A. Phase 1: Authentication (`/api/v1/auth/login`)
- **Action**: User provides credentials.
- **Response**: Returns a `selection_token` and a list of `companies` the user has access to.
- **Frontend Change**: Always check for `is_new` in the company list to trigger the "Welcome Mode" overlay.

### B. Phase 2: Selection (`/api/v1/auth/select-company`)
- **Action**: Selection of the active `company_id`.
- **Response**: Returns the final JWT (`access_token`).
- **New Claims (JWT)**:
    - `roles`: string[] (e.g., `["OWNER", "INVENTORY_MANAGER"]`)
    - `accessible_warehouses`: UUID[] (Contextual filtering for the UI)
    - `company_id`: UUID

## 2. Inventory Service: Gatekeepers & Money
### A. Readiness Gatekeeper (`GET /api/v1/readiness`)
- **OperationId**: `getInventoryReadiness`
- **Purpose**: Prevent inventory transactions if the company hasn't configured its catalogs.
- **Frontend Integration**:
    - Call this before opening the "New Document" modal.
    - If `is_ready: false`, show the checklist of pending steps to the user.

### B. Money Value Object
- **Schema**: `{ "amount": number, "currency": string }`
- **Fields Affected**: `unit_price`, `total_valuation`, `transfer_price`.
- **Frontend Change**: Use a centralized `MoneyPipe` to format prices using the ISO currency code provided in the object.

### C. Anti-Fraud & SoD (Inter-Company Transfers)
- **Rule**: A user cannot "Receive" a transfer they "Initiated" in the same company (unless they have bypass roles).
- **Error**: `403 Forbidden` with `SelfTransferReceiptException`.
- **Frontend Change**: Grey out the "Complete Receipt" button if `created_by == current_user_id` and the user doesn't have the `ADMIN` override.

## 3. Master Data Service: Global Context
- **Rule**: All requests Must include `X-Company-ID` in the header.
- **Filtering**: The backend now strictly filters variants and products by the active company.
- **Frontend Change**: Ensure the `CompanyInterceptor` is always appending the `X-Company-ID` from the auth state.

---
**FRONTEND REPOSITORY PATH**: `c:\API\interno\temp_future`

*Last Updated: 2026-03-17*
