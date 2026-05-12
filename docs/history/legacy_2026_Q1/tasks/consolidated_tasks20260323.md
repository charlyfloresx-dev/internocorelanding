# Consolidated Tasks - 2026-03-23

## ✅ COMPLETED (Today)

### 🔐 Security & Auth
- [x] **Zero Trust Auth Guard**: Implemented direct `localStorage` validation in `authGuard` to handle manual cache/storage clearing.
- [x] **AuthService Sync**: Fixed race condition in `restoreSession` for immediate signal population.
- [x] **Idempotency Headers**: Global injection of `X-Correlation-ID` in `MultiTenantInterceptor`.
- [x] **CORS Unification**: Synchronized middleware across all 4 active microservices for cross-border header support.

### 🛡️ Frontend Resilience
- [x] **Circuit Breaker Interceptor**: Graceful handling of 5XX errors from auxiliary services (Currency/Telemetry).
- [x] **Menu Fail-Safe**: `NavigationService` now defaults to Dashboard if RBAC signals are delayed or empty.
- [x] **Signal Cleanup**: `DashboardService` correctly resets telemetry on company hot-switch.

### 🗺️ User Journey Validation
- [x] **Pillar 1 (Identity)**: Multi-tenant hot-switch verified.
- [x] **Pillar 3 (Compliance)**: Binational Pedimento validation implemented and tested.
- [x] **Pillar 4 (Exceptions)**: Red Tag/WAC discrepancy UI logic confirmed in `InventoryDocumentsComponent`.

---

## 📅 PENDING / NEXT STEPS

### ☁️ Phase 35: AWS & Infrastructure
- [ ] **ECR Deployment**: Create repositories and push images for `auth`, `inventory`, `master_data`, and `currency`.
- [ ] **CloudFront Setup**: Configure S3 Bucket for Angular static hosting + CloudFront CDN with 404 rewriting.
- [ ] **Infrastructure as Code**: Finalize task definitions for ECS Fargate.

### 📈 Business Features
- [ ] **Valuation Dashboard**: Implement "Corporate Net Worth" view with real-time currency conversion (MXN/USD).
- [ ] **Audit Trail Viewer**: Frontend UI to visualize `X-Correlation-ID` chains (Forensic Observability).
