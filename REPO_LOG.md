# Interno Core - Global Engineering Log

Tracking the major milestones, architectural shifts, and technical decisions of the ecosystem.
 
### 🗓️ Mayo 2026: Motor Operacional Industrial (Tickets Service)

### [2026-05-01] Phase 76: Escalación Dinámica Multi-tenant & Soporte AI
- **Matriz de Escalación Dinámica**: Implementación de `EscalationRule` y motor de búsqueda con fallback por área (`Producción`, `Almacén`, `Soporte`, `_default`).
- **Worker Industrial (EscalationWatcher)**: Creación de un worker funcional para el escaneo de SLAs y disparo de eventos de escalación automatizada.
- **Help Center AI (Fase 8 Preview)**: Integración de lógica de auto-respuesta AI para tickets de tipo `SUPPORT` en el `TicketService`.
- **Compliance Audit**: Alcanzado 100% de cumplimiento en el `tickets_service` mediante el uso de `bypass_tenant` explícito en consultas de orquestación global.
- **HCM Alignment**: Departamentos y áreas sincronizados con los estándares de `hcm_service`.
- **Status**: ✅ Phase 76 COMPLETED — Industrial Monolith Unified & Frontend Mature.

### [2026-05-01] Phase 76: Frontend Industrialization (UI/UX Maturity)
- **Currency Support**: Implementación de `CurrencyService` y pipes reactivos para cambio dinámico USD/MXN con impacto en dashboards financieros.
- **God Mode (Modo Dios)**: Despliegue de `AdminAuthService` y `GodModeGuard` para rescate técnico y overrides administrativos.
- **Support Drawer AI**: Integración de panel de soporte lateral con gestión de tickets industriales y simulación de respuestas AI (MCP).
- **Backend Routing Remediator**: Eliminación de prefijos redundantes en `ticket_routes.py` para resolver errores 404 en el monolito unificado.
- **Support Sync Protocol**: Implementación de `/config/constants` para sincronización dinámica de enums industriales (Status, Priority, Type).
- **Reactive Support Engine**: Refactorización de `SupportService` usando Angular Signals y Effects para gestión de tickets y chat en tiempo real.
- **Industrial Localization (i18n)**: Soporte completo ES/EN para el centro de ayuda, dashboard y drawers globales.
- **Excel Mode Enhancement**: Refactorización de `InventoryDocumentComponent` para alta densidad de datos y contraste industrial.
- **Global UI Integration**: Unificación del comando global (Idioma, Moneda, Soporte) en el `MainLayout`.

### [2026-05-01] Phase 75: Tickets Service — Remediación Crítica & Expansión Operacional
- **Remediación de Precisión Financiera**: Migración de `float` a `Numeric(18, 8)` en `cost_estimate` del modelo `Ticket` y `Decimal` en DTOs para eliminar descuadres de Kardex.
- **Seguridad Inter-servicio (HMAC)**: Implementación de validación criptográfica HMAC-SHA256 en el endpoint `/internal` con logging forense de intentos no autorizados vía `AuditService.track()`.
- **Estandarización de Auditoría**: Reemplazo de `audit_repo.create_log` por `AuditService.track()` en todo el `TicketCommandHandler`.
- **Alineación de Secretos**: Corregido `SECRET_KEY` del `tickets-service` en `docker-compose.yml` (era `changeme`).
- **Subscription Seed Fix**: Extendida vigencia de suscripciones de desarrollo a 10 años (`timedelta(days=3650)`).
- **Expansión del Modelo de Dominio (Fase 5)**: 4 nuevos `TicketType` industriales (`Mantenimiento`, `Recibo Material`, `Tiempo Muerto`, `Escalación`) y 7 nuevos campos en el modelo `Ticket` (`source_service`, `station_id`, `reported_by_id`, `parent_ticket_id`, `auto_close_on_event`, `escalation_level`, `resolved_at`).
- **Self-Referential Hierarchy**: Relación `parent_ticket` ↔ `child_tickets` para cadenas de escalación.
- **CQRS Expansion**: `CreateTicketCommand` ahora propaga todos los campos operacionales al repositorio.
- **Status**: ✅ Phase 75 COMPLETED — Tickets Service Hardened & Operationally Expanded.

### 🗓️ Abril 2026: Consolidación Cloud y Resiliencia de Suscripción

### [2026-04-30] Phase 74: Bloqueo Reactivo por Suscripción & SaaS Integrity
- **Motor de Degradación L7**: Implementación de un motor de bloqueo estructurado basado en el estado de la suscripción (`PAST_DUE`, `RESTRICTED`, `UNPAID`) sincronizado entre `auth_service`, `subscription_service` e `inventory_service`.
- **Paywall Reactivo**: Los inquilinos en estado `RESTRICTED` solo tienen acceso de lectura (`402 Payment Required` en escrituras), mientras que los `UNPAID` enfrentan un bloqueo total mediante un **Global Paywall Overlay** en Angular 19.
- **Middleware Security Enforcement**: Refuerzo del `InternoCoreGlobalMiddleware` para imponer el bloqueo de seguridad basado en claims `status` y `readonly`.
- **JWT Identity Enrichment**: Inyección de claims en el JWT final y en los endpoints de `/refresh` y `/me` (Zero Trust) para hidratación de UI.
- **Reactive UI Signals (Angular 19)**: Implementación de signals `isReadOnly()` y `isUnpaid()` en el `AuthService` para bloqueo sensorial inmediato.
- **Auditoría Forense**: Validación exitosa del "cableado" de seguridad mediante `audit_subscription_states.py` (5/5 tests passed).
- **Code Graph Invariants**: Integración del invariant `SUBSCRIPTION_GUARD_VIOLATION` para detectar fugas de seguridad en microservicios de escritura.
- **Status**: ✅ Phase 74 COMPLETED — Subscription Resilience & Reactive Lockdown Operational.

### [2026-04-30] Phase 73: Estabilización de Autenticación Industrial & HCM Migration
- **HCM Service Extraction**: Despliegue del microservicio `hcm_service` bajo Clean Architecture, desacoplando la gestión de colaboradores (RRHH) del núcleo de autenticación.
- **Industrial Auth Handshake (RFID/PIN)**: Restauración del flujo de login industrial mediante escaneo de RFID (SHA-256) y PIN (Bcrypt) con descubrimiento automático de tenants.
- **JWT Identity Enrichment**: Inyección de claims operativos críticos (`full_name`, `internal_id`, `is_supervisor`, `wid`) en el JWT final, permitiendo operación Zero-Trust en dispositivos de borde.
- **Configuration Centralization**: Migración de variables críticas (como `CORE_HCM_RFID_SALT`) al `.env` global, eliminando inconsistencias entre servicios.
- **AWS CloudWatch Readiness**: Sanitización total de logs eliminando emojis y caracteres especiales para asegurar compatibilidad con AWS CloudWatch Logs.
- **Status**: ✅ Phase 73 COMPLETED — HCM Infrastructure & Industrial Auth Stabilized.

### [2026-04-28] Phase 72: Industrial WhatsApp Notifications & Virtual Group Broadcasting
- **Twilio Production Integration**: Implementación del `WhatsAppClient` con soporte para la API de producción de Twilio (Basic Auth y payloads urlencoded).
- **Virtual Group Engine**: Desarrollo de una arquitectura de "Grupos Virtuales" en el `notification_service`, permitiendo mapear un nombre lógico (ej. `ALERTAS_PLANTA`) a múltiples destinatarios individuales para superar las restricciones de Sandbox.
- **Webhook Discovery & Security**: Despliegue del endpoint `/api/v1/whatsapp/webhook` con bypass de seguridad `X-Company-ID` en el middleware global.
- **Broadcast Multitenant**: El `NotificationService` ahora procesa envíos masivos de forma atómica, registrando el estado de entrega individual.
- **Status**: ✅ Phase 72 COMPLETED — Industrial WhatsApp Pipeline Operational.

### [2026-04-18] Estabilidad Cloud AWS
- **CORS Resolution**: Se resolvió el bloqueo `400 Bad Request` ajustando el orden de carga de secretos en Python antes del montaje del middleware, solucionando la conectividad ALB.
- **Microservices Rollout**: Despliegue industrial ECS validado. Conectividad E2E desde CloudFront confirmada en el Mission Control.

### [2026-04-13] Gobernanza de Raíz
- **CORE_ Prefix**: Estandarización del prefijo de variables de entorno de `INT_` a `CORE_` y limpieza profunda del directorio raíz para evitar polución de archivos.

---

## 🏛️ Arquitectura de Identidad (SSOT)
El sistema opera bajo un protocolo de **Identidad Triple** consolidado:

| Capa de Identidad | Método de Validación | Responsabilidad |
| :--- | :--- | :--- |
| **Identidad Digital** | OAuth2 / JWT (T1/T2) | Acceso a la plataforma y APIs. |
| **Identidad Física** | RFID (SHA-256) / PIN | Operaciones en piso de producción (MES). |
| **Identidad Legal** | company_id (Multi-tenant) | Aislamiento de datos y cumplimiento fiscal. |

## 💰 Definición Financiera: La Tríada del Valor
Desde abril de 2026, el sistema rige la existencia de cualquier producto bajo una relación jerárquica estricta:
1.  **Landed Cost**: Costo de adquisición más gastos logísticos (Aduana/Flete).
2.  **CPP / WAC**: Costo Promedio Ponderado para valuación de inventario contable.
3.  **Transfer Price**: El contrato financiero sellado para movimientos entre empresas hermanas. (El precio de venta de Empresa A se convierte en el costo de Empresa B al despacho).

> [!IMPORTANT]
> **Nota de Seguridad (Zero-Trust)**: El BaseRepository captura el `company_id` directamente del JWT verificado. No se permite que el cliente envíe el ID del inquilino en operaciones de escritura para prevenir vulnerabilidades de tipo IDOR.

## 📡 Mapa de Infraestructura (Puertos Core)
| Servicio | Puerto | Función Crítica |
| :--- | :--- | :--- |
| **Monolith** | 8000 | Motor Unificado (Auth, Master, Inv, MES, Tickets). |
| **Auth** | 8001 | Microservicio (Legacy/Separate Mode). |
| **Master Data** | 8003 | Microservicio (Legacy/Separate Mode). |
| **Inventory** | 8006 | Microservicio (Legacy/Separate Mode). |
| **Subscription** | 8002 | Gestión de Billing y Lockdowns L7. |

### 🗓️ Marzo 2026: Identidad Triple y Seguridad Zero-Trust

#### [2026-03-30] Hardening de Seguridad
- **Refresh Token Rotation (RTR)**: Implementación de rotación estricta y taxonomía de tokens (access, refresh, selection).

#### [2026-03-15] Sealed Price (Precio Sellado)
- **Inmutabilidad Financiera**: Aprobación del patrón de transferencias Inter-Company: el precio de venta de la Empresa A se convierte en el costo de compra de la Empresa B al momento del despacho.

#### [2026-03-03] Estructura de Holdings
- **BusinessGroup Model**: Introducción de jerarquías para compartir catálogos maestros entre empresas del mismo grupo.

---

### Historical Archive (Legacy Phases)

### [2026-04-27] Phase 71: Financial Valuation & Forensic Audit (Ledger Stabilization)
- **Forensic Audit Engine**: Despliegue del endpoint `/api/v1/audit/` en el `inventory_service` para exponer el historial inmutable de transacciones (Ledger).
- **Audit Log UI**: Implementación del componente `InventoryAuditComponent` con visualización glassmórfica de cambios (Old vs New Value) y filtrado por acción/tabla.
- **Financial Mapping Fix**: Resolución del bug de mapeo en SQLAlchemy (`_amount` vs `unit_price`) que impedía la auditoría de movimientos financieros.
- **Notification Persistence**: Corrección del estado de lectura de notificaciones mediante auditoría de `rowcount` en el `notification_service`.
- **Multi-Currency Foundation**: Actualización de esquemas de empresa para soportar `base_currency` nativa desde el onboarding.
- **AWS Readiness**: Limpieza de strings `localhost` en configuraciones críticas, validado por Code Graph Auditor.
- **Code Graph**: ✅ 100% Compliance — 14 microservicios, 0 errores críticos.
- **Status**: ✅ Phase 71 COMPLETED — Financial & Forensic Traceability Stabilized.

### [2026-04-25] Phase 70: Interno Assets CRM & GIS Intelligence Pipeline
- **Asset Manager Service Inception**: Despliegue del microservicio `asset_manager_service` bajo Clean Architecture, integrando un motor financiero de evaluación de ROI para oportunidades inmobiliarias.
- **GIS-to-CRM Pipeline**: Implementación de `BackgroundTasks` en el `master_data_service` para la propagación automática de reportes catastrales hacia el CRM de inversiones.
- **Zero-Trust Multi-Tenancy (Personal Scope)**: Implementación de filtros por `created_by` con bypass de `company_id` para gestión de activos privados, validado 100% por el Code Graph Auditor.
- **Resiliencia de Datos (RPPC Bypass)**: Documentación de inconsistencias en el GeoServer de Tijuana y estrategia de reintentos para claves catastrales complejas (PK-020-119).
- **Kanban Dashboard UI**: Creación del módulo nativo Angular 19 (`/investments/asset-manager`) usando Angular Signals y CDK Drag&Drop.
- **Plusvalía Tooltip**: Integración del Padrón Inmobiliario 2020 vs 2026 para el cálculo en tiempo real de la apreciación del activo.
- **Seguridad RBAC**: Módulo protegido nativamente bajo el scope `investments:manage` inyectado en el NavigationService.
- **Code Graph**: ✅ 100% Compliance — 14 microservicios, 0 errores críticos.
- **Status**: ✅ Phase 70 COMPLETED — Asset Intelligence Layer Active (Backend + UI Kanban).

### [2026-04-24] Phase 69: Industrial Zero-Hardcode Frontend (SSOT Enforcement)
- **Eliminación de Mocks**: Se eliminaron los métodos `getMockWarehouses` y `getMockConcepts` de `InventoryService`, erradicando datos estáticos del flujo de inventario.
- **Resolución Dinámica de UOMs**: Se reemplazaron UUIDs quemados por una lógica de resolución por código (`PZA`, `FT`) mediante el nuevo `MasterDataService.resolveUomByCode`.
- **Limpieza de Fallbacks en Búsqueda**: `ItemSearchComponent` fue purgado de datos de ejemplo (`MAT-001`, `MAT-002`), garantizando que solo se visualicen productos reales del catálogo.
- **Staging Locations Dinámicas**: `InventoryInboundComponent` ahora genera sus puntos de estiba (*Docks*) dinámicamente desde el catálogo de almacenes, eliminando el registro estático `DOCK-01`.
- **Smart Form Preview Reactivo**: La previsualización de conceptos en el catálogo ahora utiliza almacenes reales del tenant activo para simular la lógica de negocio.
- **Intercompany Transfers UI (ICT)**: Se integró la lógica de binding de datos de dropdowns "Empresa Destino" vs "Cliente" basado en `requires_external_entity` de `TRF-EXT`.
- **Resiliencia en Documentos Financieros**: Modificación de las plantillas de `printInvoice` y `printLabel` para cast de Decimals dinámicos a Number y evitar bloqueos en el UI con `NaN` exceptions. Agregado de badges para "Pendiente de Valuación Financiera".
- **Code Graph**: ✅ 100% Compliance — 13 microservicios, 0 errores críticos.
- **Resiliencia de Excepciones**: Estandarización de `DomainException` con atributo `status_code` nativo, eliminando errores `AttributeError` en el middleware global.
- **Integración de God Mode**: Implementación del header `X-Admin-Master-Key` que permite la elevación a `GOD_MODE_ADMIN` para bypass de validaciones de propiedad multi-tenant en correcciones administrativas.
- **Middleware Guardado**: Refactorización del middleware global para manejo resiliente de errores críticos con logging forense de trazas.
- **Status**: ✅ Phase 69 COMPLETED — Zero-Hardcode & Backend Resilience Enforced.

### [2026-04-22] Phase 68: Frontend Concept-Guard Architecture (Signal-Safe Inventory Integration)

- **Signal-Safe Resolution**: `MasterDataService.resolveConceptByCode(code)` retorna `null` durante LOADING — ningún componente puede enviar `concept_id: null` al backend, eliminando errores 400/422 en cold-start de tenant.
- **Three-State Catalog Guard**: `conceptCatalogState` expone `'LOADING' | 'READY' | 'ERROR'` para que los botones de submit muestren "Configurando Empresa..." en lugar de bloquearse silenciosamente.
- **Write Guard Pattern**: `canSubmitTransfer = computed(() => isFormValid() && transferConceptId() !== null)` — patrón replicado en Transfer e Inbound.
- **Concept Injection**: `initiateInterCompanyTransfer` y `dispatchInternalTransfer` en `InventoryService` ahora tienen payloads tipados con `concept_id: string` requerido.
- **Display Duality**: Dashboard y Documentos muestran `concept_name` ("Recepción de Compra") con fallback al tipo técnico ("ENTRY") para documentos legacy.
- **Code Graph**: ✅ 100% Compliance — 13 microservicios, 0 errores críticos.
- **Status**: ✅ Phase 68 COMPLETED — Frontend Inventory Industrialization Complete.

### [2026-04-22] Phase 67.5: Master Data Concept Industrialization (Backend)
- **JIT Seeding**: `SQLAlchemyMasterDataRepository` auto-crea conceptos estándar (PUR-REC, SAL-DIS, INT-TRA) para empresas nuevas sin catálogo.
- **Inheritance Query**: Repositorios usan `OR (company_id = X, group_id = Y)` para catálogos corporativos compartidos.
- **Flow Compliance**: Los 6 scripts de flujos de inventario (`flow_1` a `flow_6`) resuelven e inyectan `concept_id` de forma dinámica.
- **Status**: ✅ Phase 67.5 COMPLETED — Backend Concept Architecture Stabilized.

### [2026-04-21] Phase 67: Hierarchical Multi-Tenancy & Master Data Visibility
- **Hierarchical Access Protocol**: Implementamos la propagación de group_id en el JWT durante la selección de empresa. Esto permite la visibilidad jerárquica de datos maestros (Catálogos Corporativos) en todos los microservicios.
- **Master Data Synchronization**: Reparación y estandarización de registros existentes en la DB (product_brands, product_categories, uoms, products). Todos los activos globales ahora están correctamente vinculados al eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e (Interno Business Group).
- **Backend Serialization Fix**: Implementación de InternoCoreEncoder en el middleware global para manejar UUID, datetime y  ytes, eliminando errores 500 en flujos de autenticación complejos.
- **Unified Industrial Seed v4**: Evolución del script de seed para poblar automáticamente la jerarquía de grupos y catálogos compartidos.
- **Status**: ✅ Phase 67 COMPLETED - Hierarchical Authorization & Visibility Stabilized.

### [2026-04-21] Phase 66: Unified Monolith & Cloud Governance (Kill Switch)
- **Monolith Pivot**: Transicionamos el entorno local a un **Monolito Unificado** (`interno-monolith`), consolidando 11 microservicios en un solo motor de alto rendimiento.
- **FinOps Kill Switch (Cloud Janitor)**: Implementación de `backend/scripts/infraestructure_aws/99_nuke_everything.ps1`, un mecanismo de demolición total para llevar la factura de AWS a **$0.00** de forma instantánea.
- **AWS Orchestrator**: Creación de `backend/scripts/infraestructure_aws/01_deploy_full_stack.ps1` para el re-ensamblaje automatizado de la infraestructura (VPC-Bridge + PrivateLink).
- **Subscription Guard (Kill Switch v1)**: Desarrollo del middleware `SubscriptionGuard` que implementa el modo "Solo Lectura" (Soft Kill Switch) para proteger la integridad de los datos en caso de suscripciones vencidas.
- **Infraestructure State**: Documentación del estado **LOCAL ONLY** en `INFRASTRUCTURE_STATE.md` con guías de recuperación.
- **Status**: ✅ Phase 66 COMPLETED - Governance & Performance Stabilized.

### [2026-04-20] Phase 65: FinOps App Runner Isolation & AWS Service Quotas
- **App Runner Deployment refactor**: Transicionamos la validación de AWS desde despliegues manuales en CLI atados a la cuenta de GitHub hacia un enfoque `Amazon ECR` nativo, optimizando los costos de despliegue mediante AWS App Runner.
- **Service Quotas Discovery**: Se descubrió una cuota oculta ("Anti-Fraude") de AWS en cuentas nuevas que restringe App Runner a un máximo de **2 servicios simultáneos**. Se abrió Ticket Support `#177671606300742` a Operaciones de AWS para incrementar la cuota a 5 y acomodar la flota Microservicios completa.
- **Limpieza Estratégica**: Se ejecutó limpieza via CLI eliminando `notification-service` y recursos bloqueados para priorizar de forma elástica la disponibilidad del `master-data-service` y el `auth-service` dentro del límite de 2 slots actual.
- **Status**: ⏳ Phase 65 PAUSED - Pending AWS Support Quota Approval (ETA < 24h).

### [2026-04-20] Phase 63: High Operational Availability (Laissez-Faire) & Density Guard
- **Recepción Laissez-Faire**: Refactorización del flujo de entrada de mercancía para priorizar la continuidad operativa. El sistema ahora responde con **202 Accepted** de forma inmediata, delegando la validación a tareas de fondo.
- **Density Guard Asíncrono**: Implementación de auditoría silenciosa que valida la capacidad física de las ubicaciones sin bloquear la transacción. Registra estados de `OVERFLOW_CONFIRMED` en el Ledger para visibilidad gerencial.
- **Centralización de Master Data**: Migración definitiva de `InventoryLocation` al `master_data_service` como única fuente de verdad (SSOT) estructural.
- **Arquitectura Reactiva**: Activación de eventos `CapacityViolationEvent` hacia el `notification_service` para alimentar alertas en tiempo real en el Dashboard principal.
- **Compliance DB (Alembic)**: Despliegue de la migración `fe63_val_status` para soportar estados de validación en el ledger de movimientos.
- **Status**: ✅ Phase 63 COMPLETED - Reactive Industrial Logic Online.

### [2026-04-20] Phase 64: Visibility Stress-Test & Resilience
- **E2E Validation**: Successfully executed the "Stress-Test de Visibilidad" injecting a 500-unit overflow into a 10-unit location.
- **Notificación Industrial**: El `notification_service` procesó correctamente la alerta `CapacityViolationEvent`, persistiendo el estado en el Dashboard de Control.
- **Hardenning**: Corregidos fallos de integridad multitenancy y esquemas faltantes en el motor de notificaciones.
- **Status**: ✅ FASE 64 E2E VALIDATION: PASSED.

### [2026-04-20] AWS Budget Pivot: ALB to App Runner
- **Optimización de Costos**: El Application Load Balancer (ALB) fue identificado como un gasto excesivo (~$23 USD/mes base) para el presupuesto de $5.00 USD.
- **Acción**: Eliminación del ALB e infraestructura de ECS Fargate residual. Transición hacia **AWS App Runner** (PaaS) para el `auth_service`.
- **Infraestructura**: Creado `apprunner.yaml` y guía de despliegue `APP_RUNNER_DEPLOY_GUIDE.md` para estandarizar el despliegue de bajo costo.
- **Status**: ✅ Phase 58 COMPLETED - Low-Cost Infrastructure Pivot.

### [2026-04-18] Phase 57: GIS Integration & Tijuana Cadastral Mapping
- **GIS Core Integration**: Desarrollo de `ArcGisTijuanaProvider` en `common/gis` para validación de claves catastrales y georeferenciación frente al IMPLAN Tijuana.
- **Web Scraping de Propietarios**: Implementación de scraping resiliente con manejo de `__VIEWSTATE` para recuperar el nombre del propietario legal desde el portal de pagos de Tijuana.
- **ValueObject Address**: Enriquecimiento del objeto de dirección con `cadastral_key`, coordenadas y tipo de propiedad, manteniendo compatibilidad con servicios existentes.
- **Status**: ✅ Phase 57 COMPLETED - GIS & Cadastral Validation Online.

### [2026-04-18] AWS Cloud Stability & CORS Resolution
- **Problema de CORS (Mixed Content vs Preflight)**: Se resolvió que el bloqueo `400 Bad Request` en producción provenía del orden de carga en Python (Starlette evalúa CORS antes de que `boto3` inyecte secretos).
- **Resolución**: Arquitectura ajustada invirtiendo Imports para que AWS Secrets (`load_aws_secrets`) parchee `int_backend_cors_origins` antes de que el middleware sea montado, solucionando instantáneamente la conectividad ALB.
- **Microservices Rollout**: Despliegue industrial ECS validado. Conectividad E2E desde CloudFront confirmada en el Mission Control.
- **Status**: ✅ Phase 55 STABILIZED - Production Auth Service Online & Verified.

### [2026-04-17] Phase 55: AWS Industrial Deployment & Frontend CDN
- **Microservices**: `auth_service` desplegado en AWS ECS Fargate us-east-2.
- **Infrastructure**: ALB validado, RDS conectado, Secret Injection implementado.
- **Frontend**: Angular build corregido con `fileReplacements` y desplegado en CloudFront.
- **Docs**: Creados `MICROSERVICE_DEPLOY_GUIDE.md` y reportes de estatus.
- **Status**: ✅ Phase 55 COMPLETED - Auth & Frontend Production Ready.

## [2026-04-16] - Phase 44: Infrastructure Convergence & Media Assets support
- **Unified Cloud Abstraction (`StorageProvider`)**: Engineered a strategy-pattern based storage library in `backend/common`. Supports multi-tenant S3 (AWS/LocalStack) and Local storage with a single interface. Implemented automatic Pre-signed URL generation for secure, high-speed frontend retrieval.
- **SSM Configuration Resilience**: Established a hierarchical Parameter Store structure (`/interno-core/global/` vs `/interno-core/{service}/`) to deduplicate global secrets. Validated migration through de-duplication scripts and LocalStack (v1.4.0) integration to bypass AWS Pro license requirements.
- **Microservice Media Expansion (RH, Inventory, Master Data)**: Scaled the industrial photo pattern across the ecosystem. Engineered `VariantService` to handle asset logic in `inventory_service` and updated `master_data_service` for catalog photos. Applied targeted Alembic schema synchronization to ensure multi-tenant RDS integrity for digital assets.
- **Frontend URL Normalization**: Developed an Angular `imageInterceptor` and `secureImage` Pipe to handle multi-tenant asset paths. The system automatically injects the primary assets domain (`environment.assetsUrl`) and handles default placeholders, ensuring a premium UX regardless of deployment mode.
- **Logistics Cleanliness (Gobernanza)**: Moved all operational test and migration scripts to `backend/tests/integration/infrastructure/` to maintain a zero-pollution root directory.
- **Status**: ✅ COMPLETED (Cloud-Ready, Media-Enabled & Scaled Backbone)

## [2026-04-15] - Phase 53: Industrial Data Simulation Injection
- **Data Scaling for UI Validation**: Engineered a direct SQLAlchemy integration bypass (`simulate_liquor_distro.py`) to inject highly dense logic scenarios without relying on API controllers. 
- **Simulated RBAC**: Explicitly wired 3 multi-tenant roles testing boundaries: `tony@interno.com` (Group Admin), `garry@interno.com` (Distributor Logistics), and `tropy@interno.com` (Single Node Operator) to fully evaluate Angular Component un-mounting and guarded routing.
- **Kardex Injection**: Simulated over 15 days of continuous operations (+180 entries) involving IN, OUT, and ADJUSTMENT operations pushing pricing valuation logic (WAC bounds) specifically targeted towards forensic audit rendering scenarios.
- **Status**: ✅ COMPLETED (High Volume QA Environment Ready)

## [2026-04-15] - Phase 49.8: Outbound Shipping & Compliance (Embarques Industrial)
- **Shipping Handheld Module**: Launched `InventoryShippingComponent` (`/inventory/shipping`) completing the warehouse loop. The module validates scanned Folios from the Picking stage and prepares the dispatch manifest.
- **Anexo 24 Driver Validation**: Integrated a mandatory "Driver Badge Scan" step as a bridge to Phase 50 (`hr_service`). This ensures that only authorized personnel with valid cross-border credentials (Visa/Sentry) can authorize international material dispatch.
- **WMS Menu Integration**: Registered "Embarques" as the final stage in the `NavigationService` and Dashboard quick-access loops.
- **Status**: ✅ COMPLETED (Full Warehouse Loop Closed)

## [2026-04-15] - Phase 49.5: Handheld UI Stabilization & Surface Refresh
- **Theme Unification**: Refactored all handheld modules (`Inbound`, `Picking`, `Put-Away`, `Cycle-Count`) to consume global Design System tokens (`surface-bg`, `surface-card`, etc.). Hardcoded dark-mode hex values were eliminated to support the system's dynamic Light/Dark mode toggles.
- **Full-Width Responsiveness**: Optimized industrial layouts for wide-aspect ratios (i.e. iPad Pro/Industrial Tablets). Standardized screen containers to `max-w-4xl` for better touch-target balance and visual hierarchy in desktop/tablet environments.
- **Manual Entry Restoration**: Rescued the "Blind Entry" and "Scan-less" flows in the handhelds, ensuring operators can recover from damaged barcodes while maintaining audit integrity.
- **Status**: ✅ COMPLETED (Industrial UX Optimized for Modern Hardware)

## [2026-04-15] - Phase 49: Cycle Count & Audit Sheets (Auditoría Total)
- **Blind Count Module**: Developed `CycleCountComponent` with a 3-step industrial flow: Location Lock → Blind Scan (no theoretical data shown) → Discrepancy Analysis. Operator scans SKUs individually; quantity adjustments via +/- controls. All validated against `InventoryRegistryService` ($O(1)$).
- **Audit Sheet Export**: Backend CSV generator (`/warehouses/{id}/audit-export`) with UTF-8-BOM encoding for Excel compatibility. Columns include Location, SKU, Pedimento (Anexo 24), and a blank "Physical Check" column for floor auditors.
- **Supervisor Override**: Discrepancies exceeding 5% of theoretical quantity require `supervisor` or `admin` role to confirm, enforcing segregation of duties on inventory adjustments.
- **Navigation Integration**: Added quick-access card ("Auditoría Spot") to Inventory Dashboard and sidebar entries in both Inventarios and WMS/Logística menus.
- **Status**: ✅ COMPLETED (Physical-to-Digital Reconciliation Enabled)

## [2026-04-15] - Phase 48: Industrial Integrity & "The Density Guard"
- **The Density Guard (Capacity Safety)**: Implemented a robust physical safety layer. Created `InventoryLocation` models with `max_capacity` constraints. The backend now performs real-time occupancy calculations (SUM of FIFO balances) and blocks movements (IN/RELOCATE) that exceed physical limits, raising `ERR_LOCATION_OVERFLOW`.
- **Registry Cache ($O(1)$ Search)**: Optimized the handheld experience for large-scale operations (10k+ SKUs). Developed an in-memory registry hydration system in Angular, ensuring SKU validation and metadata retrieval are instant, eliminating network-induced barcode delay.
- **Visual & Audio Feedback**: Integrated a semantic progress bar (Green/Amber/Red) in the Put-away flow to visualize rack utilization. Added an industrial overflow beep (110Hz) to notify operators of capacity violations without looking at the screen.
- **Legacy Port (Data Hygiene)**: Ported and modernized the `getNumber` regex logic from the .NET legacy codebase to sanitize scanner inputs, automatically stripping invisible characters and hardware-injected suffixes.
- **Status**: ✅ COMPLETED (Physical Integrity & Low-Latency Verified)

## [2026-04-15] - Phase 47: Industrial Put-Away & Session Stability
- **Handheld Put-Away Module**: Developed and integrated the `InventoryPutAwayComponent` with a specialized "3 Scans" flow (Origin -> Destination -> Confirm). Optimized for industrial scanners with F2 hotkey support and square-wave audio feedback (200Hz/880Hz).
- **Session Resilience Engine**: Patched critical session loss bugs by implementing defensive `getattr` lookups in the Auth service and a "Resilient Parsing" layer in the Angular frontend to handle varying microservice response structures (Double-Wrap Fix).
- **Anexo 24 Compliance Lock**: Enforced automated `pedimento_id` inheritance in internal relocations, ensuring 100% legal traceability from DOCK-01 to final RACK position.
- **Mission Control Integration**: Added quick-access industrial cards to the Dashboard for the multi-tenant warehouse operator.
- **Status**: ✅ COMPLETED (Warehouse Cycle Closed & Session Resilient)

## [2026-04-15] - Phase 46: Industrial Logistics Scalability & Anexo 24 Compliance
- **Server-Side Scalability**: Implemented unified pagination (`limit`/`offset`) and global search filters in `InventoryService` (Backend). The system is now architecture-ready for 10,000+ SKU catalogs.
- **Handheld UX Stabilization**: Resolved build-breaking Angular compilation errors (ESBuild compatibility) and standardized industrial UI aesthetics for stock audit views.
- **Standardized API Metadata**: Evolved `ApiResponse` model to include `total_count`, providing foundation for paginated reports across the ecosystem.
- **Logistics Integrity**: Fixed JSON parsing bottlenecks and ensured token-aware service integration for warehouse operators.
- **Handheld Response Resilience**: Implemented a 300ms RxJS debounce mechanism in terminal search bars to protect Backend resources during high-speed industrial scanning.
- **Status**: ✅ COMPLETED (Inventory Backbone hardened for Industrial Scale)

## [2026-04-14] - Phase 46: Industrial Pricing Pipeline Finalization
- **Secure Ticket Bridge**: Migrated the binational pricing system from fragile Blob downloads to a robust, session-based ticket mechanism (`/export/ticket`). UUID tokens guarantee isolation and cryptographic access.
- **Native File Naming (Suffix Hack)**: Successfully bypassed Chrome's Cross-Origin `window.location.href` naming restrictions by injecting a dummy suffix (`/plantilla.csv`) and refactoring Angular's `MasterDataService` to forcefully overlay the generic `.csv` name on background-downloaded blobs.
- **In-Memory Validation**: Verified standard CSV loads with 15+ articles confirming that 1.5KB real prices are pulled and formatted securely by the Backend core. Tested and approved Soft-Close Insert architecture via Drag & Drop pipeline in `price-import-dashboard.component.ts`.
- **Status**: ✅ COMPLETED (Catalog Pricing fully industrialized and deployable)

## [2026-04-14] - Phase 45.1: Pricing Stabilization & B2B Immortality (Final)
- **Immutable Pricing Logic**: Finalized the **"Soft-Close & Insert"** pattern for B2B price agreements and master prices, ensuring 100% auditability for industrial contracts. Validated via direct DB queries (Time-Torn timestamps).
- **Complexity Resolution**: Fixed critical `500 Internal Server Errors` (`AttributeError` on `amount`) in `master_data_service` by bridging Pydantic/SQLAlchemy composite `Money` mapping with native Python `@property` decorators on ORM variables (`ProductPrice`). Resolved `NotNullViolationError` by strictly enforcing `current_user.company_id` onto `tenant_id` namespace explicitly.
- **Enterprise Templates**: Generated official `plantilla_carga_precios_industrial.csv` for standardized mass-imports across multiple hierarchy vectors (List 0-10, Agreements).
- **Hybrid Pricing Interface**: Completed the tabbed UI for `ProductPriceListComponent`, integrating live partner alerts and premium "Missing Data" tooltips.
- **Quality Assurance**: Integrated `pytest` suite for automated pricing validation and patched `aiosqlite` for in-memory testing of complex Postgres-specific models (UUIDs).
- **Status**: ✅ COMPLETED (Pricing Infrastructure Hardened & Verified)

## [2026-04-14] - Phase 45: Industrial Pricing & Identity Stabilization (Frontend UX & RBAC)
- **SSOT UI RBAC Enforcement**: Standardized the `scopes` validation on `navigation.service.ts` aligning strictly with the `ROLE_SCOPE_MAP` backend injection map (`inv:movements:manage`, `master:catalog:manage`, `wms:manage`). 
- **Dynamic Scope Resolution**: Hardcoded scope mapping was decoupled from `auth_service.app.commands.select_company_command`. Scopes are now dynamically generated via `ROLE_SCOPE_MAP` mapping roles to UI sidebar modules, including `["*"]` logic for administrators.
- **Pricing Matrix UX Refactor**: Re-engineered `product-price-list.component.ts` layout using industrial flex-box standards. Implemented fixed header and sticky `ic-modal-body` constraints to resolve `max-height: 90vh` rendering overflow glitches.
- **Master Data Integrity Check**: Finalized `master_product_id` schema logic generation utilizing Python `uuid5` cross-service standard generation, guaranteeing binational entity ID tracking.
- **RBAC Catalog**: Added `rbac_scopes_catalog.md` defining strict constraints over `permissions` (backend logic) VS `scopes` (frontend UI menus).
- **Status**: ✅ COMPLETED (Ecosistema Totalmente Mapeado y Estabilizado)

## [2026-04-13] - Phase 44: Industrial Pricing & B2B Contracts
- **Inmutabilidad Industrial (Soft-Close)**: Se blindó el maestro de precios prohibiendo ediciones directas. Todo cambio genera una nueva versión inmutable con sellado de tiempo, garantizando auditoría "Point-in-Time".
- **Engine de Acuerdos B2B**: Implementación de la jerarquía de precios: Contrato > Lista > Maestro. Integración del modelo `PriceAgreement` para condiciones comerciales específicas por Partner.
- **Control Tower de Importación**: Desarrollo de un pipeline atómico de carga masiva en el backend y dashboard Drag & Drop en el frontend (Angular 18). Soporte para templates dinámicos y reporteo forense de errores.
- **Compliance DB (Alembic)**: Despliegue seguro de esquemas para multi-tenancy inmutable sin impactar la data existente.
- **Status**: ✅ COMPLETED (Ecosistema Financiero Estabilizado)

## [2026-04-13] - Phase 43: Root Governance & Global Standardization

- **Global Rename (CORE_ Prefix)**: Se estandarizó el prefijo de todas las variables de entorno de `INT_` a `CORE_` en microservicios, dockers, scripts y documentación para evitar colisiones semánticas.
- **Estructura de Directorios & Backend Cleanup**: 
    - Scripts operativos movidos a `scripts/`. Reportes y logs consolidados en `logs/`. Documentación categorizada en `docs/`.
    - Sanitización profunda de `backend/`: Eliminación de 8+ archivos huérfanos (`.log`, `.txt`, `.json`) y carpetas redundantes (`backend/backend`).
    - Separación del historial en `docs/historial/tasks` e `implementation`.
- **Exclusión de Kiosk**: El proyecto se re-enfoca exclusivamente en el núcleo industrial MES/ERP. Las tareas de eventos han sido archivadas y marcadas como fuera de alcance.
- **Premium Web Documentation**: Creación de `docs/DOCS_INTERNOCORE.html` como portal web de alta fidelidad enfocado exclusivamente en el núcleo MES/ERP (Industrial Backbone).
- **Workflow Updates**: Actualización de los agentes de sincronización para operar bajo la nueva jerarquía de archivos y el estándar de variables `CORE_`.
- **Status**: ✅ COMPLETED (Ecosistema Estandarizado e Industrializado)

## [2026-04-12] - Phase 42.5: Event Engine Generalization & N-Approver Quórum
- **Universal Engine**: El sistema evolucionó de un modelo de "Bodas" a un **Motor de Trabajo de Eventos Universal**. Se reemplazaron los roles fijos por un sistema de **Quórum de $N$ Aprobadores** dinámicos totalmente configurable.
- **Blindaje de Base de Datos (Alembic Async)**: Implementación de migraciones versionadas asíncronas para el `kiosk_service`. Eliminada la dependencia de recreación manual de tablas, permitiendo actualizaciones de esquema seguras y automáticas mediante `alembic upgrade head` durante el arranque.
- **Filtro de Integridad (Identity Protection)**: Incorporación de validación por `device_id` en el backend para garantizar votos únicos por hardware físico, evitando suplantaciones en el proceso de moderación.
- **Mecanismo de Emergencia "Staff Reset"**: Funcionalidad de autocuración que permite al Staff reiniciar el ciclo de votación (Quórum) de cualquier foto defectuosa o errónea.
- **Status**: ✅ COMPLETED (Industrial Ready for Offline Mini-PC)

## [2026-04-11] - Phase 42: Event Kiosk Initialization & Smart Checkout
- **Infrastructure**: Se configuró un orquestador ligero (`docker-compose.kiosk.yml`) exclusivo para eventos, interconectando `postgres-db`, MinIO, y el nuevo `kiosk-service` con límites de memoria estrictos para Mini PCs.
- **Match System (Tinder Mode)**: Lógica de aprobación fotográfica dual (Novio y Novia) en el backend y cliente Angular 19 (PWA).
- **Checkout Híbrido**: Arquitectura *One-Intent* consolidando compras de carrito e integrando Monedero Paparazzi interno con Stripe Elements.
- **Hardware Integration (CUPS & Print Daemon)**: Worker asíncrono para consumir estados `PURCHASED`, aplicar recorte 3:2 DNP y volcado directo al spool de linux vía `pycups`.
- **Status**: ✅ COMPLETED (Binomial Digital-Physical Verified)

## [2026-04-03] - Phase 41.5: UI Consolidation & Industrial Readiness
- **Dynamic Binational Guard**: Implementada lógica inteligente basada en códigos de país (MX/US) en el frontend.
- **Modo Permisivo Industrial**: Configuración del formulario en modo "Warning-Only" para evitar bloqueos operativos por falta de metadata aduanera no crítica.
- **Status**: ✅ COMPLETED

## [2026-04-01] - Phase 39: Auth Proxy & Kiosk Integration
- **Collaborator Login Handshake**: Integrated `auth_service` with `hr_service`. Supports secure proxy where Auth issues JWT after HR verifies physical credentials (RFID/PIN).
- **O(1) Physical Scans**: Database indexing optimized for SHA-256 RFID hashes, ensuring sub-10ms response times for high-volume entry/exit.
- **Status**: ✅ COMPLETED

## [2026-03-26] - Phase 38: HR Microservice Bootstrap
- **Service Extraction**: Decoupled HR logic from Auth into `hr_service` with dedicated `hr_db`.
- **Infrastructure**: Added healthchecks and automated migrations for HR ecosystem.
- **Status**: ✅ COMPLETED

## [2026-03-25] - Phase 37: HR Microservice Inception
- **Architectural Shift**: Transitioned from Monolithic Auth to SRP-based identity management.
- **Warehouse Lock Concept**: Defined zero-trust barriers for physical inventory operations.
- **Status**: ✅ COMPLETED

## [2026-03-24] - Phase 35: Multi-Tenant Data Consistency & CORS Stabilization
- **Data Homologation**: Synced Company IDs across all 11 services (Enterprise, Logistics, Demo).
- **Master Seed Orchestration**: Automated multi-tenant seeding via `master_seed.py`.
- **CORS Permissiveness**: Resolved preflight (OPTIONS) blocks by unifying allowed headers.
- **Status**: ✅ COMPLETED

## [2026-03-15] - Phase 30: Refresh Token Rotation (RTR) & Security
- **Token Taxonomy**: Implemented `typ` claim (access/refresh/selection) to prevent token misuse.
- **Refresh Token Rotation**: Engineered SHA-256 backed RTR to detect and block replay attacks.
- **Status**: ✅ COMPLETED

## [2026-03-07] - Phase 19: Clean Architecture Enforcement
- **Repository Pattern**: Standardized `IRepository` interfaces across Inventory and Master Data.
- **Dependency Injection**: Implemented automated resolution for service-to-repository mapping.
- **Status**: ✅ COMPLETED

## [2026-03-04] - Phase 4: Traceability & Governance (Guardianship)
- **Governance**: Refactored `MultiTenantBase` inheritance for strict auditor compliance.
- **Traceability**: Integrated `X-Trace-Id` for forensic tracking of login attempts.
- **Status**: ✅ COMPLETED

## [2026-03-03] - Phase 3: Cluster Structures (Holdings)
- **Holding Support**: Introduced `BusinessGroup` model for shared visibility in Master Data.
- **Corporate Context**: Injected `group_id` claim in JWT for cross-company transfers.
- **Status**: ✅ COMPLETED

## [2026-02-25] - Phase 2: Subscription & Entitlements
- **Interconnectivity**: Synchronized `auth_service` with `subscription_service`.
- **Read-Only Mode**: Implemented enforcement for expired tenant subscriptions.
- **Status**: ✅ COMPLETED

## [2026-02-12] - Phase 1: Foundation & T1/T2 Handshake
- **Protocol Inception**: Implementation of OAuth2 Password Flow.
- **Dual-Step Auth**: Engineered the `/login` (T1) and `/select-company` (T2) flow for multi-tenant environments.
- **Standardization**: Established UUIDv5 as the deterministic standard for cross-service entity mapping.
- **Status**: ✅ COMPLETED (Ecosystem Birth)

*(End of historical log)*