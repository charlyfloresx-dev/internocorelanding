# Consolidated Tasks - 2026-03-17

## Status Overview
- **Phase**: 33.2 (Inter-Company Trust)
- **Overall Progress**: 85% for Inventory Module

## Completed Today ✅
### Backend (Inventory & Master Data)
- [x] Implement `GetCompanyInventoryReadinessHandler` (Gatekeeper logic).
- [x] Add `/readiness` endpoint to Inventory API.
- [x] Create internal readiness check endpoints in Master Data (UOM, Products, Pricing).
- [x] Update `seed.py` with Mirror Document sample and Physical warehouses.
- [x] Add `/api/v1/inventory/levels` and `/api/v1/inventory/folio-preview/{concept_id}`.

### Frontend (Angular)
- [x] Create `InventoryReadinessGatekeeperComponent`.
- [x] Integrate Gatekeeper into `InventoryDashboardComponent`.
- [x] Implement `physicalWarehouses()` computed signal for selector filtering.
- [x] Add "Espejo ICT" visual badge for mirror documents.
- [x] Transition `InventoryService` from Simulation to Real API.

## Pending Tasks ⏳
### Phase 34: AWS Infrastructure & Deployment
- [ ] Create ECR Repositories for backend microservices.
- [ ] Configure S3 + CloudFront for Frontend distribution.
- [ ] Define VPC Network isolation and IAM roles (Strategy drafted).

### Final Stabilization
- [ ] Implement approval workflow for DRAFT ICT documents (recepción física).
- [ ] Sync `partnerships` catalog from Master Data to Inventory UI (currently hardcoded placeholder).
- [ ] Verify `loadWarehouseCatalogs` in production environment (Docker).

## Next Priority
1. **ECR Push**: Push the current validated Docker images to AWS ECR.
2. **CloudFront Setup**: Initialize the CDN for the Frontend to testing SPA routing behavior.
