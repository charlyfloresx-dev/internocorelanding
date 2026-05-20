# InternoCore Common Library - SERVICE LOG

> **Library:** InternoCore Common
> **Status:** Stable / Universal Ecosystem Core
> **Responsibility:** Standardizing Cross-Cutting Concerns (Security, Config, Audit, Models)

---

### [2026-05-20] - Phase 117: Namespace Scope Matching Security Bridge ✅

- **`security/dependencies.py`**: Added `_scope_satisfies` helper inside `require_scope` dependency. Resolves authorization mismatches where endpoints require coarse scopes (e.g. `master_data:read`) but tokens carry granular database permission slugs (e.g. `master_data.product.read`).
  - Supports namespace matching (e.g., prefix `master_data` matching suffix `read` or `write`).
  - Automatically maps `manage` suffix to both `read` and `write`.
  - Maintains strict exact matches and wildcard `*` fallback for admin roles.
- **Status**: ✅ COMPLETED — Tested and validated E2E.

---

### [2026-05-19] - Phase 116: SubscriptionGuard JTI Gate ✅

- **`security/subscription_guard.py`**: Added Redis JTI lookup for god_mode tokens. `SubscriptionGuard.__call__` now checks `GET godmode:{jti}` when `token_data.god_mode=True`. Token revoked in Redis → 401. Redis unavailable → pass (fail-open, JWT TTL ≤300s as fallback).
- **`domain/entities/user_context.py` / `security/auth_payload.py`**: Fields `jti: Optional[str]` and `god_mode: bool` added to `TokenPayload`. Required for JTI gate and god_mode interceptor in Angular frontend.
- **Status**: ✅ COMPLETED — SubscriptionGuard + get_current_active_user both gate on JTI. Smoke test 9/9 passed.

---

### [2026-05-19] - Phase 115: TokenPayload god_mode fields ✅

- **`security/auth_payload.py`**: Fields `jti: Optional[str]` and `god_mode: bool = False` added to `TokenPayload`. Enables Angular `godModeInterceptor` and SubscriptionGuard JTI gate to function correctly.
- **`config.py`**: No changes — god_mode credentials validated via existing `CORE_ADMIN_MASTER_KEY`.
- **Status**: ✅ COMPLETED — JWT payload extended without breaking existing token consumers.

---

### [2026-05-18] - Phase 113: Security Hardening Sprint 1 ✅

- **`config.py`**: Eliminado `default="GOD_MODE_ACTIVE"` del `Field`. Sin `CORE_ADMIN_MASTER_KEY` en el entorno el proceso falla al arrancar (fail-closed). `@field_validator` bloquea valores trivialmente débiles y longitud < 16.
- **`middleware.py`**: `bypass_tenant` usa `_settings.int_admin_master_key` en lugar del string literal hardcodeado. `/admin/elevate` agregado a `is_public_route`.
- **`infrastructure/database.py`**: RLS hook blindado — UUID validado antes de interpolación, `connection_record.invalidate() + raise` en lugar de `except: pass`.
- **`services/audit_service.py`**: `log_action()` extendida con `ip_address` y `user_agent` opcionales → mapeados a `AuditLog.client_ip` / `AuditLog.user_agent`. Eliminado `print()`.
- **`security/subscription_guard.py`**: GOD MODE emite `logger.critical` + `AuditService.log_action()` en cada activación. `getattr` fallback eliminado.
- **Status**: ✅ COMPLETED — 0 CRITICALs en Code Graph.

---

### [2026-05-18] - Phase 112: RequirePermission Guard ✅

- **`require_permission.py`**: Nuevo guard `RequirePermission(slug, module_code="auto")` en `common/security/`. Callable class compatible con `Depends` de FastAPI. Compone sobre `SubscriptionGuard` — valida JWT + módulo de suscripción + readonly mode, luego verifica el slug granular contra `token.scopes`. Auto-resolución de `module_code` por prefix del slug (`inventory.*` → `INVENTORY_CORE`, `pos.*` → `INVENTORY_CORE`, `master_data.*` → `MASTER_DATA_CORE`, `hcm.*` → `HCM_CORE`, `admin.*` → `AUTH_CORE`). Wildcard bypass para `scopes=["*"]`. Exportado desde `common/security/__init__.py`.
- **Status**: ✅ COMPLETED — 0 CRITICALs en Code Graph. Listo para aplicar en endpoints de alta sensibilidad.

---

### [2026-04-16] - Phase 44: Infrastructure Convergence & Storage ✅
- **Status**: ✅ COMPLETED — **Universal Cloud Abstraction**
- **Unified Storage Provider** (`infrastructure/storage/provider.py`):
  - Created `StorageProvider` abstract interface.
  - Implemented `S3StorageProvider` (Boto3/Pre-signed URLs) and `LocalStorageProvider`.
  - Exported through `common.__init__` for single-line microservice consumption.
- **SSM-Ready Config** (`config.py`):
  - Added hierarchical storage tokens: `CORE_STORAGE_BACKEND`, `CORE_S3_ENDPOINT`, `CORE_S3_BUCKET`, `CORE_LOCAL_STORAGE_PATH`.
  - Standardized environment-to-SSM mapping via `AliasChoices`.
- **Deduplication Logic**: Consolidated global environment variables (`CORE_DATABASE_URL`, `CORE_SECRET_KEY`) into the `/interno-core/global/` namespace for AWS cost optimization.
- **Architectural Polish**: Moved integration test scripts to `backend/tests/integration/infrastructure` to prevent root pollution.

---

### [2026-04-14] - Phase 45: Global Security Convergence ✅
- **Status**: ✅ COMPLETED — **Zero Trust Unification**
- **Unified Middleware**: Merged `TenantSecurityMiddleware` logic into `InternoCoreGlobalMiddleware`. The core now handles request tracing, public route whitelisting, and multi-tenant cross-validation in a single high-performance pass.
- **AWS Standard Config**: Refactored `InternoSettings` to use `AliasChoices` with `CORE_` prefix. This enables 11 microservices to inherit cloud-ready configuration patterns by default.
- **Public Route Sanitization**: Fixed a critical trailing slash bug in the middleware whitelist that was causing false-positive 400 Bad Request errors on root endpoints.

---

### [2026-04-13] - Phase 43: Naming Standard Convergence ✅
- **Status**: ✅ COMPLETED
- **CORE_ Variable Migration**: Renamed all internal settings from `INT_` to `CORE_` to avoid semantic collisions with cloud providers and third-party libraries.
- **Audit Field Homogenization**: Standardized `created_by` and `updated_by` across the `MultiTenantBase` model, ensuring consistent UUID handling for admin vs collaborator users.

---

### [2026-04-01] - Phase 39-42: Binational Foundation ✅
- **Status**: ✅ COMPLETED
- **Binational Enums**: Unified `CountryCode` and `Currency` enums to support MX/US operations across all domains.
- **Base Repository Hardening**: Implemented the automatic `company_id` filter in `BaseRepository` for a fail-closed multi-tenant security model.
- **Global Response Schema**: Standardized the `{"status", "data", "message", "meta"}` response pattern for consistent frontend interceptor handling.
