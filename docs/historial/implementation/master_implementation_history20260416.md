# Master Implementation History - 2026-04-16

## Session Summary: Industrializing Cloud-Readiness & Storage

**Goal**: Establish a Low-Cost AWS infrastructure simulation (Phase 44) and modernize HR service with multi-tenant asset management.

### Technical Decisions & Achievements

1.  **Low-Cost SSM Strategy (De-duplication)**:
    *   **Logic**: Identified redundant variables across 10+ services (DB URLs, Stripe Keys).
    *   **Solution**: Implemented a hierarchical SSM Parameter Store structure (`/interno-core/global/` vs `/interno-core/{service}/`).
    *   **Simulation**: Configured LocalStack to emulate SSM. Resolved license blockers by pinning to Community version 1.4.0 and using `Type='String'` (free tier safe).

2.  **Unified Storage Architecture (`StorageProvider`)**:
    *   **Pattern**: Factory pattern in `backend/common` providing `S3StorageProvider` or `LocalStorageProvider`.
    *   **Tenant Segregation**: Enforced S3 Key prefixing: `{company_id}/{module}/{subpath}`.
    *   **Frontend Prep**: Integrated Pre-signed URL generation via Boto3.

3.  **HR Service Modernization (Collaborators)**:
    *   **Model/Entity**: Added `photo_path` to `Collaborator` (SQLAlchemy + Domain Entity).
    *   **Feature**: Enabled optional photo upload in `POST /` endpoint.
    *   **Resilience**: Implemented Fail-Safe storage (logs errors but doesn't block DB commitment).

4.  **Inventory & Master Data Synchronization**:
    *   **Scaling Pattern**: Replicated the `RH` storage pattern to `Inventory Service` and `Master Data Service` in record time.
    *   **Features**: Enabled product photos (Catalog) and variant photos (Warehouse Items).
    *   **Repository decoupling**: Introduced `VariantService` to handle asset logic without bloating repositories.
    *   **Self-Healing Migrations**: Applied targeted Alembic revisions to sync RDS schemas across services.

5.  **Frontend Asset Normalization**:
    *   **Interceptor**: Created `imageInterceptor` to prepend `assetsUrl` to relative paths in API responses.
    *   **UX**: Added `secureImage` Pipe for easy template rendering with default placeholders.

### Blockers Resolved
- **LocalStack Pro Block**: Fixed exit code 55 by downgrading image to 1.4.0 and avoiding Pro-only services (SecretsManager) / features (SecureString).
- **Circular Dependencies**: Fixed in `kiosk_service` by extracting Enums to a dedicated domain layer.

### New Config Tokens (CORE_ prefix)
- `CORE_STORAGE_BACKEND`
- `CORE_S3_ENDPOINT`
- `CORE_S3_BUCKET`
- `CORE_LOCAL_STORAGE_PATH`
- `CORE_S3_PUBLIC_URL`
- `CORE_S3_ACCESS_KEY` / `CORE_S3_SECRET_KEY`
