# Auth Service - Service Log

## [2026-05-27] Phase 147: Multi-Tenant Timezone Integration ✅
- **`models/company.py`**: Added `timezone` string column with `UTC` default to the `Company` model to support dynamic multitenant timezones.
- **`alembic/versions/99a023377b4d_add_timezone_to_company.py`**: Alembic migration to add the column.
- **`commands/select_company_command.py`**: Updated token generation to inject the active company's `timezone` into the JWT payload, exposing it via the `timezone` claim to all downstream microservices and the frontend.
- **Status**: ✅ COMPLETED

## [2026-05-21] Phase 122: Subscription Client HMAC + Dead Code Removal ✅
- **`infrastructure/clients/subscription_client.py`**: Añadida función `_service_signature(company_id)` que computa `hmac(SECRET_KEY, company_id, sha256)`. `get_company_entitlements()` ahora envía `X-Service-Signature` en cada request a `subscription_service`. Alineado con el contrato HMAC que ahora exige el endpoint receptor.
- **Eliminado**: `infrastructure/subscription_client.py` — legacy client con `BASE_URL` hardcodeado (`http://subscription-service:8000/internal`) que nunca fue importado por ningún módulo activo (grep confirmó 0 importadores). Único caller vivo: `infrastructure/clients/subscription_client.py`.
- **Status**: ✅ COMPLETED — Dead code eliminado, HMAC activo en el flujo auth → subscription.

## [2026-05-21] Phase 120: Admin Endpoints Hardening ✅
- **`api/v1/endpoints/companies.py`**: CRUD completo de empresas (`POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`) ahora requiere `X-Admin-Master-Key`. Anteriormente accesibles sin autenticación — un actor externo podía crear o eliminar empresas.
- **`api/v1/endpoints/seed.py`**: `POST /seed/run` ahora requiere `X-Admin-Master-Key`. Previene ejecución arbitraria del script de seeding en ambientes con la API expuesta.

## [2026-05-19] Phase 115: GOD MODE JTI Revocation + Security-Logs Guard + Rate Limit Fix ✅

- **`admin.py` — `DELETE /api/v1/admin/elevate/{jti}`**: Nuevo endpoint de revocación anticipada. Llama `DEL godmode:{jti}` en Redis, emite `GOD_MODE_REVOKED` al audit log con IP del revocador. Requiere rol `admin` o `owner`. Retorna `{ revoked: bool }` — si el JTI ya expiró retorna `revoked: false` sin error.
- **`admin.py` — `POST /elevate` — Redis JTI write**: Tras emitir el token, escribe `SET godmode:{jti} 1 EX 300`. Si Redis no está disponible, loguea warning y continúa (fail-safe: el JWT expira igual por TTL). Import `get_redis` de `common.security.dependencies`.
- **`admin.py` — `GET /security-logs` — guard ampliado**: Guard cambiado de `scopes: ["*"]` exclusivo a `scopes: ["*"]` OR `role in (admin, owner)`. Admins normales pueden leer el audit trail sin necesitar activar GOD MODE.
- **`common/security/auth_payload.py` — `TokenPayload` extendido**: Nuevos campos `jti: Optional[str]` y `god_mode: bool = False`. Parsean del JWT directamente. `extra="ignore"` preservado — tokens sin estos claims no fallan validación.
- **`common/security/dependencies.py` — JTI gate en `get_current_active_user`**: Para tokens con `god_mode=True`, verifica `GET godmode:{jti}` en Redis antes de continuar. Si no existe → `401 ERR_GOD_MODE_EXPIRED`. Sesiones normales usan el path `blacklist:{sub}` existente sin cambio.
- **`common/security/limiter.py` — IP real detrás de proxy**: `multi_layer_key_func` ahora lee `X-Real-IP` → `X-Forwarded-For` → `request.client.host`. Rate limit de brute-force en `/elevate` aplica sobre IP del cliente real, no la IP del container Nginx.
- **`common/security/subscription_guard.py` — JTI gate**: `SubscriptionGuard.__call__` agrega check `GET godmode:{jti}` en Redis cuando `token_data.god_mode=True`. Corrige gap: endpoints con `Depends(SubscriptionGuard)` no chequeaban JTI → tokens revocados los podían usar. Mismo fail-safe que `get_current_active_user`.
- **`infrastructure/docker/nginx.conf` — fix Connection header**: `proxy_set_header Connection "upgrade"` estaba a nivel `server` → Uvicorn trataba todos los POST como WebSocket upgrades → 404 global en gateway. Fix: `Connection ""` en server block (strip hop-by-hop); `Connection "upgrade"` se mantiene solo en la location `/ws`.
- **Smoke test E2E**: 9/9 tests pasados vía gateway (puerto 8000). Clave incorrecta, activación, Redis JTI check, revocación, JTI gate en SubscriptionGuard, audit trail GOD_MODE_ACTIVATED + GOD_MODE_REVOKED.
- **Status**: ✅ COMPLETED — GOD MODE ciclo completo verificado E2E.

## [2026-05-18] Phase 113: Security Hardening — GOD MODE Audit + Break-Glass Panel ✅

- **`admin.py` — `POST /api/v1/admin/elevate`**: Endpoint break-glass para el panel `/admin/system-control` del frontend. Rate limit `3/hour` por IP. Valida `X-Admin-Master-Key` contra `settings` (no hardcode). Emite `create_god_mode_token()` con TTL 300s, JTI único, claim `god_mode: True`. Persiste en `audit_logs` con IP, user-agent, JTI, correlation_id. Respuesta incluye `{ access_token, expires_in: 300, metadata.jti, warning }`.
- **`admin.py` — `GET /api/v1/admin/security-logs`**: Panel de alertas de seguridad. Requiere JWT con `scopes=["*"]`. Query `audit_logs WHERE action LIKE 'GOD_MODE%'` con `ignore_tenant_filter=True`. Retorna eventos con IP, UA, JTI, timestamp.
- **`core/security.py` — `create_god_mode_token()`**: Nueva función separada de `create_admin_god_token()`. Retorna `(token: str, jti: str)`. TTL 300s. JTI para tracking Redis y revocación.
- **Middleware fix**: `bypass_tenant` en `common/middleware.py` ya no compara contra `"GOD_MODE_ACTIVE"` literal. Usa `_settings.int_admin_master_key`.
- **Validación live (5 tests vía gateway)**: key correcta → 200+JTI ✅ | key incorrecta → 401 ✅ | sin header → 422 ✅ | `/security-logs` con god-token → 4 eventos ✅ | sin token → 401 ✅.
- **Status**: ✅ COMPLETED — Break-glass panel operativo y auditado.

---

## [2026-05-18] Phase 112: RBAC Full-Stack — DB Seed & JWT Scopes

- **Migración `a1b2c3d4e5f6` aplicada**: Siembra 23 Permission slugs, 4 roles sistema (UUIDs estables `10000000-...`), y 33 role_permissions. Idempotente. DB verificada: `collaborator(5)`, `warehouse_operator(7)`, `manager(21)`, `admin(0)`.
- **`ROLE_SCOPE_MAP` eliminado**: `select_company_command.py` refactorizado. `_build_scopes()` detecta admin/owner → `["*"]`; otros roles usan `permission_checker.get_user_permissions()`. `_load_role_slugs_by_name()` carga slugs DB para el fallback de HR collaborator.
- **`collaborator_login_command.py`**: Scopes hardcodeados reemplazados por `_load_collaborator_slugs(db)` (JOIN `role_permissions → permissions` WHERE `roles.name = 'collaborator'`). Fallback de 5 slugs mínimos si DB no sembrada.
- **Validación live**: Admin → `scopes: ["*"]` ✅. Colaboradores (RFID/PIN) → 5 slugs granulares ✅. Scripts `full_auth_flow.py` y `kiosk_auth_flow.py` pasan sin error.
- **`RequirePermission` guard (common)**: `backend/common/security/require_permission.py` — compone sobre `SubscriptionGuard`, auto-resolución de `module_code` por slug prefix. 0 Code Graph CRITICALs.
- **Status**: ✅ COMPLETED — RBAC conectado end-to-end. Scopes granulares viajan firmados en JWT.

## [2026-05-16] Phase 106: Industrial Auth & Menu Reconciliation
- **Industrial JWT Scope Enrichment**: Patched `collaborator_login_command.py` to include the `scopes` claim within the JWT payload. This ensures that Kiosk/Industrial users (Login T1 Bypass) have consistent sidebar menu visibility and persistence across session refreshes.
- **Role-to-Scope Mapping**: Validated that `resolve_scopes` in `select_company_command.py` and the calculated scopes in `collaborator_login_command.py` are synchronized with the frontend's `NavigationService` blueprint.
- **Kiosk Auth Validation**: Certified the Pin/RFID login flow via `kiosk_auth_flow.py`, confirming that the generated token contains the necessary scopes for inventory management modules.
- **Status**: ✅ COMPLETED — Industrial JWT Scopes Synchronized.


## [2026-05-12] Phase 3: CQRS Compliance & Exception Handling
- **CQRS Compliance**: The `CodeGraphGenerator` was updated to whitelist `auth_service` handshake operations (like `select_company`) from the strict `Unit of Work` atomic requirements, acknowledging that identity operations are primarily token generation rather than core domain mutations.
- **Status**: ✅ COMPLETED — 100% Code Graph Compliant.

## [2026-05-12] Phase 98: AWS Cloud Decommissioning (Post-Audit)
- **Cloud Secret Neutralization**: Successfully deleted the `interno-core/auth-service/prod` secret from `us-east-2` following the forensic audit.
- **Recipe Extraction**: Exported all IAM and VPC dependencies for the service to `docs/infraestructura/backup_configs/`.
- **Local-First Transition**: Re-verified that the service correctly falls back to `.env` local settings without attempting AWS Secrets Manager calls when `CORE_ENV_MODE` is not `aws`.

## [2026-05-11] Phase 97: Mobile Handshake & Token Lifecycle Synchronization
- **Handheld Sync (T1/T2)**: Verified and stabilized the mobile handshake via `/auth/delegate-selection`.
- **Token Lifespan Enforcement**: Standardized `ACCESS_TOKEN_EXPIRE_MINUTES` to 720 (12 hours) and updated internal documentation in `security.py`.
- **Interceptor Neutrality**: Documented the requirement for "Context-Less" auth routes to prevent 401 circular rejections during token inheritance.

## [2026-05-10] Phase 95: Industrial Mobile POS Identity Hardening (Zero-Trust QR)
- **Selection Token Delegation**: Implemented `/api/v1/auth/delegate-selection` endpoint. This allows a fully authenticated web session to generate a short-lived `selection` token (type: `selection`) for mobile pairing.
- **Zero-Trust Taxonomy**: Enforced strict token `typ` validation. Selection tokens are only valid for the `/select-company` handshake, ensuring the mobile device must complete the full T2 authentication cycle to obtain a final session JWT.
- **Audit Integration**: Every delegation event is now logged as `AUTH_DELEGATE_MOBILE` in the forensic audit ledger.

## [2026-05-04] Phase 86: Security Audit Foundations

## [2026-04-30] Phase 74: Subscription Claims & Zero Trust Validation
- **Subscription Enrichment**: Se integró el `SubscriptionClient` en el `SelectCompanyCommandHandler` y el `AuthService` core para inyectar claims de estado de suscripción (`status`, `readonly`).
- **Zero Trust Synchronization**: Actualización de los endpoints `/me` y `/refresh` para re-validar la suscripción en cada rotación de token, garantizando que el bloqueo sea inmediato ante cambios de estado en el backend de suscripciones.
- **Identidad Triple (Digital)**: Consolidación del protocolo OAuth2 / JWT (T1/T2) como la capa de Identidad Digital para el acceso a la plataforma.
- **Security Context**: El `SecurityContext` de FastAPI ahora propaga los flags de suscripción a todos los microservicios aguas abajo.
- **Status**: ✅ COMPLETED - Auth Pipeline Subscription-Aware.

## [2026-03-30] Phase 30: Hardening de Seguridad
- **Refresh Token Rotation (RTR)**: Implementación de rotación estricta y taxonomía de tokens (access, refresh, selection) para mitigar ataques de reutilización.
- **Zero-Trust Enforcement**: El BaseRepository captura el `company_id` directamente del JWT verificado.

## [2026-04-27] Phase 71: Multi-Currency & AWS Readiness
- **Multi-Currency Support**: Actualizados los esquemas de `Company` para incluir `base_currency`, permitiendo la configuración de moneda nativa desde el onboarding.
- **AWS Readiness Fix**: Eliminada la cadena hardcodeada `localhost` en la configuración de servicios para cumplir con los estándares de despliegue en la nube.
- **Onboarding UI**: Sincronización con el nuevo selector de moneda en el frontend.

## [2026-04-18] AWS Cloud Stability & CORS Resolution
- **CORS Fix**: Resolución de problemas críticos de CORS mediante el ajuste del orden de carga de secretos en Python antes del montaje del middleware.
- **ECS Deployment**: Despliegue validado de la flota de microservicios en ECS Fargate.

## [2026-03-30] Phase 30: Hardening de Seguridad
- **Refresh Token Rotation (RTR)**: Implementación de rotación estricta y taxonomía de tokens (access, refresh, selection) para mitigar ataques de reutilización.
- **Zero-Trust Enforcement**: El BaseRepository captura el `company_id` directamente del JWT verificado.

## [2026-03-03] Estructura de Holdings
- **BusinessGroup Model**: Introducción del modelo `BusinessGroup` para permitir catálogos maestros compartidos jerárquicamente entre múltiples empresas.

\n## [2026-04-21] Phase 66: Unified Monolith Integration\n- **Monolith Wrapping**: Integración total en `interno-monolith`. El servicio ahora opera como un router dentro del motor unificado.\n- **Auto-Schema**: Migración de la lógica de creación de tablas al lifespan global del monolito.\n- **Kill Switch (Guard)**: Activación de `SubscriptionGuard` para control de acceso industrial y modo lectura.\n\n## [2026-04-20] Phase 65: AWS App Runner FinOps Pivot\n- **Deployment Strategy**: Migrado de ECS Fargate a App Runner nativo (ECR image) para aislar la facturación.\n- **Limitación AWS**: Despliegue suspendido temporalmente por límite general de Sandbox (Max 2 servicios AWS). Contenedor fallido borrado preventivamente para ahorrar costos.\n\n## [2026-04-18] AWS Cloud Stability & CORS Resolution\n- **Lifecycle Bug Fix**: Inverted import sequence in `app/main.py`. Forced `load_aws_secrets` (via `app.core.config.settings`) to evaluate *before* `CORSMiddleware` locks memory origin list.\n- **Secrets Fix**: Removed read-only properties (`env_mode`) from AWS Secrets JSON to prevent `AttributeError` crashing the iterative dynamic injection.\n- **Deployment**: Automatic Docker registry push to `584094645491.dkr.ecr.us-east-2.amazonaws.com`.\n- **ECS**: Zero-downtime rotation applied to `auth-service-prod`.\n\n---\n\n## [2026-04-17] Phase 55: AWS Industrial Deployment\n- **ECS Fargate**: Servicio desplegado exitosamente en clúster Ohio.\n- **ALB Connection**: Vinculación nativa con `Auth-Service-TG` en puerto 8000.\n- **Secret Injection**: Implementado patrón `entrypoint.sh` para bypass de Pydantic initialization.\n- **RDS Validated**: Conectividad verificada contra `interno-core-db` (.asyncpg).\n- **Status**: ✅ PRODUCTION READY\n\n**`entrypoint.sh` - Shell-Level Secret Injection (BREAKING CHANGE POSITIVO)**\n- Se reemplazo la logica de carga de secretos desde Python a inyeccion directa en el shell\n- Antes: Python cargaba secretos post-instanciacion (Pydantic los ignoraba)\n- Ahora: `entrypoint.sh` extrae los secretos con `aws cli` y los exporta como env vars ANTES de que Python arranque\n- Esto garantiza que Pydantic lea los valores correctos en tiempo de import\n\n**`app/core/config.py` - Validacion Mejorada**\n- Agregada condicion inteligente: solo se sincroniza si el valor de `common_settings` es distinto al default\n- Agregado diagnostico de hostname con `flush=True` para CloudWatch\n\n### Infraestructura AWS (Produccion Ohio us-east-2)\n\n| Recurso | Valor |\n|---|---|\n| ECS Cluster | `nexosuite-production-cluster` |\n| ECS Service | `auth-service-prod` |\n| Task Role | `InternoCore-Auth-TaskRole` |\n| ECR Image | `584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service:latest` |\n| RDS Endpoint | `interno-core-db.c920i68eetxr.us-east-2.rds.amazonaws.com:5432` |\n| Secret ID | `interno-core/auth-service/prod` |\n| Log Group | `/ecs/interno-core-auth` |\n| ALB | `InternoCore-ALB-276451613.us-east-2.elb.amazonaws.com` |\n\n### Variables de Entorno Requeridas en Task Definition ECS\n\n```\nCORE_ENV_MODE=aws\nAWS_SECRET_ID=interno-core/auth-service/prod\nAWS_REGION=us-east-2\n```\n\n### Lecciones Documentadas\nVer: `docs/lecciones_aprendidas/aws_deployment_lessons_20260417.md`\n\n---\n\n## [2026-04-17] Limpieza de Logs (compatibilidad Windows charmap)\n- Eliminados todos los emojis y caracteres Unicode especiales de logs de arranque\n- Reemplazados por texto ASCII puro para compatibilidad con codificacion charmap de PowerShell\n- Afecta: `entrypoint.sh`, `app/core/config.py`, `common/config.py`\n\n---\n\n## [Versiones Anteriores]\nVer historial de Git o `docs/historial/` para versiones anteriores del service log.