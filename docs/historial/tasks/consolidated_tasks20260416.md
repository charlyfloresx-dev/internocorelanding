# Consolidated Tasks - 2026-04-16

## ✅ COMPLETED

### Infrastructure (Phase 44 - Low Cost)
- [x] **SSM De-duplication**: Script `migrate_to_ssm.py` developed and validated.
- [x] **LocalStack Setup**: `docker-compose.localstack.yml` configured and running with S3 and SSM.
- [x] **Telemetry**: Prometheus sidecar with 7-day retention policy (`7d`) configured.
- [x] **Storage Provider**: Unified `common` provider for S3/Local storage.

### HR Service
- [x] **Collaborator Photos**: Database and Domain support for `photo_path`.
- [x] **Photo Upload**: Integerated storage logic in `create_collaborator`.
- [x] **API Output**: Automatic Pre-signed URL generation for frontend.

### Frontend (Angular)
- [x] **Image Interceptor**: Automatic normalization of asset URLs.
- [x] **SecureImage Pipe**: Placeholder and absolute path handling.
- [x] **Environment Config**: Base `assetsUrl` configuration.

### Kiosk Service
- [x] **Architectural Alignment**: Decoupled models from schemas by extracting domain enums.

## 🚧 IN PROGRESS
- [ ] **Auth Service SSM Integration**: Transitioning from `.env` to dynamic SSM lookup.
- [ ] **MinIO / moments.com Resolution**: Testing local DNS for Fargate parity.

## 📅 PENDING (Next Session)
- [ ] **Inventory Service Storage**: Integrate `StorageProvider` for product variants.
- [ ] **CloudFront Strategy**: Define final deployment paths for assets.
- [ ] **Stripe Centralization**: Migrate all services to use global /interno-core/global/ SSM keys.
