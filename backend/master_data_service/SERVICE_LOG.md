### [2026-04-21] Phase 66: Unified Monolith Integration
- **Monolith Wrapping**: Integración total en `interno-monolith`.
- **SSOT Enforcement**: El servicio ahora actúa como la fuente única de verdad para ubicaciones físicas (`InventoryLocation`) y almacenes dentro del motor unificado.
- **Auto-Sync Metadata**: Sincronización automática de modelos `Product`, `Warehouse` y `Location` mediante el motor global.

### [2026-04-20] - Phase 65: AWS App Runner FinOps Pivot
- **Deployment**: Migración de `master-data-service` a App Runner (`584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/master-data-service`).
- **Bloqueo AWS**: Contenedor provisto exitosamente pero bloqueado (CREATE_FAILED) por Sandbox AWS Quota limit (2). Servicio removido preventivamente por FinOps.

### [2026-04-14] - Phase 45.1: Pricing Stabilization & B2B Immortality ✅
- **Status**: ✅ COMPLETED — **Reliable Pricing Architecture**
- **Composite Mapping Fix**: Resolved `AttributeError: 'ProductPrice' object has no attribute 'amount'` by implementing python property bridges for `amount` and `currency` in the SQLAlchemy model.
- **Tenant Validation Strictness**: Resolved `NotNullViolationError` for `tenant_id` by explicitly propagating the company context in mass import endpoints.
- **B2B Agreement Lifecycle**: Fully implemented the "Soft-Close & Insert" pattern for `PriceAgreement` records, ensuring 100% auditability for contract-specific pricing.
- **Verification**: Zero-trust multi-tenant prices validated via direct DB forensics.

### [2026-04-14] - Phase 45: AWS Standard Configuration & Cloud Readiness ✅
- **Status**: ✅ COMPLETED — **Industrial Cloud Parity**
- **Cloud-Ready Config**: Refactored `config.py` to use `AliasChoices` with the `CORE_` environmental prefix, enabling seamless integration with AWS Secrets Manager.
- **Unified Security Interface**: Synchronized shared configuration with the `InternoSettings` master class, inheriting global security and tenant-isolation patterns.
- **Database Connection Sanitization**: Standardized `ASYNC_DATABASE_URL` property to handle `postgresql://` to `postgresql+asyncpg://` transitions automatically across different environments.

### [2026-04-13] - Phase 44: Industrial Pricing & B2B Agreements ✅
- **Status**: ✅ COMPLETED
- **Price Immutability (Soft-Close)**: Full implementation of versioned pricing. Updates seal the current record via `valid_until` and insert new rows. Prohibited in-place updates of `amount`.
- **B2B Contracts**: Integrated `PriceAgreement` model for entity-specific commercial conditions (Partners).
- **Mass Import Pipeline**: Atomic processing of CSVs for general and B2B pricing, including automatic `IVA_Flag` Master Data sync.
- **Dynamic Templates**: Dynamic CSV generation for tenant-wide prices and specific partner contracts.

### [2026-04-10 EOD] - Phase 33.6: RBAC Governance & Industrial Fast-Entry ✅

- **Status**: ✅ COMPLETED
- **RBAC Enforcement**: Se aplicaron guards de rol (admin/owner) en todos los endpoints de escritura de Categorías, Marcas y UOMs.
- **Pricing Immutability**: Implementación del modelo de precios con soporte para 'Soft-Close' (valid_until) y flags de auditoría manual, permitiendo un histórico inmutable de cambios de precio por SKU.
- **Fiscal Compliance**: Extensión del esquema ProductCreate para capturar códigos SAT/HTS y estados fiscales (is_taxable) desde el alta inicial.
- **Incomplete Product Support**: Soporte backend para creación parcial de productos (solo SKU/Nombre/UOM requeridos) para alimentar el dashboard de completitud del frontend.

---

# 📜 Master Data Service - SERVICE LOG

> **Service:** Master Data Service (Port 8003)
> **Status:** Active / SSOT for Products & UOMs

---

### [2026-03-24] - Phase 35: Multi-Tenant Data Consistency & CORS Stabilization ✅
- **Status**: ✅ COMPLETED — **The Single Source of Truth is Sane**
- **Data Homologation**: Sincronización de IDs de empresas y usuarios en el catálago maestro para asegurar que las consultas cross-service devuelvan información coherente en el dashboard.
- **Master Seed Orchestration**: Participación en el flujo de `master_seed.py`, garantizando que todas las empresas tengan sus UOMs, marcas y categorías base creadas con IDs determinísticos.
- **CORS & Preflight Fix**: Configuración de `allow_origins=["*"]` e incorporación de headers de selección y trazabilidad (`X-Selection-Token`, `X-Correlation-ID`) para garantizar interoperabilidad con el frontend.

### [2026-03-23] - Phase 34: CORS Unification & Idempotency Support ✅
- **Status**: ✅ COMPLETED
- **Features**: Sincronización de políticas CORS para soportar trazabilidad industrial.
- **Detalles técnicos**: Se actualizó el `CORSMiddleware` para permitir explícitamente el header `X-Correlation-ID` y asegurar que las peticiones OPTIONS (preflight) desde el navegador sean aceptadas sin fricción durante cambios de contexto.

### [2026-03-17] - Phase 33.3: Readiness Assessment Support ✅
- **Status**: ✅ COMPLETED
- **Features**: Implementación de endpoints de diagnóstico masivo para soportar el Gatekeeper de Inventarios.
- **Detalles técnicos**:
  - **Readiness APIs**: Nuevos endpoints `check_uom_readiness`, `check_product_readiness` y `check_pricing_readiness` que permiten a otros servicios validar la configuración mínima de un tenant velozmente.
  - **Performance**: Optimización de queries de conteo para validación de catálogos base.
  - **Refactor**: Sincronización de la interfaz `IMasterDataClient` con el modo estricto de Pyre2.
  - **Seeder**: Actualizado `seed.py` para garantizar que los datos demo cumplen con los criterios del Gatekeeper (UOM Pieza, Productos cargados y precios base).

### [2026-03-12] - Phase 25.4: Frontend Hard Validation Integration ✅
- **Status**: ✅ COMPLETED
- **Features**: Exposed `requires_external_entity` and `requires_target_warehouse` flags properly initialized in MovementConcepts to the frontend.
- **Impact**: Enables deterministic front-end blocking logic.

### [2026-03-12] - Phase 25.3: Master Data Consolidation & Audit Pro ✅
- **Status**: ✅ COMPLETED
- **Models**: Unified `Product` with legacy attributes and added forensic flags. Implemented `Warehouse`, `MovementConcept`, and `UOMConversion`.
- **Infrastructure**: Integrated SQLAlchemy event listeners for automated, immutable audit logging.
- **Seeding**: Populated global UOMs, conversions, and movement concepts.
- **Compliance**: 100% aligned with Audit Engine Pro standards.

### [2026-03-07] - Phase 19: Clean Architecture Enforcement ✅
- **Status**: ✅ COMPLETED (Auditor 100% OK)
- **Repository**: Implemented `IMasterDataRepository` and `SQLAlchemyMasterDataRepository` for all 5 services (`Product`, `Brand`, `Category`, `UOM`, `Sync`).
- **Dep. Injection**: Added `repositories.py` dependency for automated interface resolution.
- **Results**: 0 DB Leaks detected by `generate_code_graph.py`.

---

### [2026-03-06] - Phase 16: Stabilization & Governance Restoration ✅
- **Status**: ✅ COMPLETED
- **Governance**: Restored `MultiTenantBase` inheritance across all models (`UOM`, `Product`, etc.).
- **Persistence**: Resolved `version_id` mapping collisions by explicitly disabling optimistic locking where conflicting with legacy schema.
- **OpenAPI**: Successfully extracted `master_data.json` spec.
- **Compliance**: Validated via Code Graph (**0 Errors**).

### [2026-03-04] - Auditoría de Interoperabilidad (Fase 6 Prep)
- **Modelo UOM**: Se verificó que `conversion_factor` sea `Float` para permitir cálculos de inventario precisos entre diferentes unidades.
- **Seguridad**: Confirmada la validación de registros globales mediante el `SYSTEM_USER_ID` verificado en la última corrida del seeder unificado.
- **Clean Architecture**: Eliminación de referencias circulares hacia `inventory_service`.

### [2026-03-04] - Phase 23: Audit Compliance & UOM Remediation
- **Audit**: Refactored `UOM` model to include `conversion_factor` as required by the audit protocol.
- **Identity**: Standardized `SYSTEM_USER_ID` to `00000000-0000-0000-0000-000000000000` in seed scripts.
- **Governance**: Verified inheritance from `MultiTenantBase` and `AuditBase` to ensure `version_id` and audit fields performance.

### [2026-02-13] - FASE 11: Estabilización y Cableado de Master Data
- **Saneamiento Estructural**: Creación de carpetas `db/` y `schemas/`, y normalización de paquetes mediante archivos `__init__.py`.
- **Implementación de Catálogos**: Creación de `catalogs.py` (Enums ISO/SAT) y el router `master.py`.
- **Performance**: Ajuste de `DATABASE_URL` para soporte de `asyncpg`.

### [2026-02-12] - FASE 10: Creación de Master Data Service
- **Nacimiento**: Creación del microservicio para gestionar Productos, UM, Categorías y Marcas.
- **Dominio**: Implementación de modelos `Product`, `ProductVersion`, `ProductCategory`, `UM` con soporte de i18n (`translation_key`).
- **Versiones**: Diseño de la lógica para soportar versiones paralelas de productos.

 # #   2 0 2 6 - 0 3 - 3 0 :   M u l t i t e n a n t   E x p a n s i o n   &   I n t e r - c o m p a n y   T r a n s f e r s 
 -   U p d a t e d   W a r e h o u s e   m a p p i n g   i n   A P I   t o   i n c l u d e   ' c o m p a n y _ i d '   f o r   f r o n t e n d   g r o u p i n g . 
 -   R e f a c t o r e d   s e e d   s c r i p t   t o   s u p p o r t   t w o   s e p a r a t e   l e g a l   e n t i t i e s :   M X   a n d   U S   L o g i s t i c s . 
 -   V e r i f i e d   s u c c e s s f u l   i n t e g r a t i o n   o f   b i n a r y   c o u n t r y   l o g i c   f o r   w a r e h o u s e s .  
 
