# Auth Service - Service Log

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