### [2026-06-02] Phase 168 — Endpoints Bulk Import para Onboarding Wizard ✅

- **`schemas/product.py`**: `ProductBulkItem` + `ProductBulkResult` añadidos.
- **`api/v1/endpoints/products.py`**: `POST /products/bulk` — resuelve UOM por code y categoría por nombre ILIKE, idempotente por `(company_id, sku)`, siembra `ProductPrice` lista-1 si `unit_price` presente. Rate limit 20/min. Scope `master_data:write`.
- **`schemas/partner.py`**: `PartnerBulkItem` (con `rfc` como alias de `tax_id`, `city` fallback para `address`) + `PartnerBulkResult`.
- **`api/v1/endpoints/partners.py`**: `POST /partners/bulk` — idempotente por `(company_id, code)`. Rate limit 20/min. Scope `master_data:write`.

---

### [2026-06-02] Phase 168 — PENDIENTE (pre-implementación): Contratos de API ⚠️

> **Contexto:** El Onboarding Wizard Angular (Phase 167, `frontend/src/app/modules/auth/onboarding.component.ts`) llama a dos endpoints de este servicio que aún **no existen**. Los contratos abajo son el contrato definitivo acordado para implementación.

#### A. `POST /api/v1/products/bulk` — FALTA IMPLEMENTAR

**Propósito:** Importación masiva de productos desde CSV en el paso 3 del wizard de onboarding.

**Contrato JSON esperado:**
```json
{
  "products": [
    {
      "sku": "SKF-6205",
      "name": "Cojinete SKF 6205",
      "description": "Cojinete radial estándar",
      "category_tag": "Mantenimiento",
      "uom_code": "PZ",
      "base_price": { "amount": 45.00, "currency": "MXN" },
      "warehouse_assignments": [
        {
          "warehouse_code": "WH-MAIN-01",
          "custom_price": { "amount": 45.00, "currency": "MXN" },
          "initial_stock": 150
        }
      ]
    }
  ]
}
```

**Notas de implementación:**
- `company_id` siempre del JWT (nunca del payload — previene IDOR).
- Cada ítem usa `ProductCreate` schema internamente. Idempotencia por `(company_id, sku)` — upsert si ya existe.
- `warehouse_assignments.initial_stock > 0` → disparar `POST /api/v1/inventory/bulk-load` con `X-Internal-Secret` header en inventory_service (bypass rate-limit). Es HTTP inter-servicio, NO FK cruzada.
- Errores por ítem se acumulan en `results.errors[]` — el bulk NO se aborta por fallas individuales (UX deliberada: onboarding ≠ data migration crítica).
- Scope: `master_data:write`. Rate limit: `20/minute` (operación cara).
- **Alineación con onboarding.service.ts**: el service actualmente envía `{ items: rows }`. Al implementar el endpoint, o bien el endpoint acepta ambas claves (`products` ó `items`) o se actualiza el service a `{ products: rows }`.

**Ruta de registro en `main.py`:** incluir en el router de `products` existente como sub-ruta.

---

#### B. `POST /api/v1/partners/bulk` — FALTA IMPLEMENTAR

**Propósito:** Importación masiva de clientes/proveedores desde CSV en el paso 4 del wizard.

**Contrato JSON esperado:**
```json
{
  "partners": [
    {
      "code": "PROV-001",
      "name": "Maquiladora ACME S.A. de C.V.",
      "type": "SUPPLIER",
      "tax_id": "ACM900101AB1",
      "email": "ventas@acme.com.mx",
      "phone": "664-123-4567",
      "address": "Av. Producción 1024, Tijuana, BC, MX 22000"
    }
  ]
}
```

**Mapeo CSV → Modelo `Partner`:**
| Campo CSV (onboarding template) | Campo ORM `Partner` | Notas |
|---|---|---|
| `code` | `code` | Unique per `company_id` |
| `name` | `name` | |
| `type` | `type` (`PartnerType` enum) | `SUPPLIER` / `CUSTOMER` / `BOTH` |
| `rfc` | `tax_id` | El template llama al campo `rfc` pero el ORM usa `tax_id` |
| `email` | `email` | |
| `phone` | `phone` | |
| `city` | concatenar en `address` | El modelo tiene `address: String(500)` flat, no objeto anidado |

**Notas de implementación:**
- Idempotencia por `(company_id, code)` — skip duplicados con warning, no error.
- Validación binacional: si `tax_id` tiene formato RFC mexicano (13 chars) → ok. Si es EIN/Tax ID US → aceptar como string libre.
- Scope: `master_data:write`.
- **Alineación con onboarding.service.ts**: el service envía `{ items: rows }`. Al implementar, aceptar `partners` o `items` como clave raíz, o actualizar el service.

---

### [2026-05-28] Phase 152: Scan Pattern Validation per Item ✅
- **`models/product_scan_pattern.py`**: Nuevo modelo `ProductScanPattern` (tabla `master_product_scan_patterns`). Campos: `item_code`, `pattern_name`, `regex`, `error_message`, `priority`, `is_active` (heredado). UniqueConstraint por `(company_id, item_code, pattern_name)`. Índice compuesto `(company_id, item_code, is_active)`.
- **`schemas/product_scan_pattern.py`**: `ScanPatternRead`, `ScanPatternCreate`, `ScanPatternUpdate`.
- **`schemas/product.py`**: `ProductRead` extendido con `scan_patterns: List[ScanPatternRead] = []`.
- **`services/product_service.py`**: `lookup_product_by_code()` carga patrones activos ordenados por `priority` y los embebe en `ProductRead.scan_patterns` (evita 2do HTTP call en scan latency-critical).
- **`api/v1/endpoints/product_scan_patterns.py`**: CRUD REST: `GET /{item_code}/scan-patterns` (scope `master_data:read`), `POST` con validación de regex vía `re.compile()`, `PATCH`, `DELETE` (soft-delete: `is_active=False`). Rate limit 30–60/min.
- **`alembic/versions/b5c2d3e4f5a6_add_product_scan_patterns.py`**: Migración aplicada ✅.
- **`main.py`**: Router registrado en `/api/v1/products`.
- **Fix**: `ScanPatternCreate.item_code` eliminado del body schema (el endpoint lo recibe por path param, evitaba 422).
- **Status**: ✅ COMPLETED — 0 CRITICAL en Code Graph. Tabla verificada en `master_data_db`.

### [2026-05-27] Phase 147: Multi-Tenant Timezone Integration ✅
- **`alembic/versions/a6b1698e23e1_add_timezone_to_company.py`**: Alembic migration to add the `timezone` string column with `UTC` default to the `companies` table, matching the identity definition in `auth_service`.
- **Status**: ✅ COMPLETED

### [2026-05-24] Phase 131: PAYMENT_METHOD en enumerations + sync master_data_db ✅
- **`scripts/seed_enums.py`**: `PAYMENT_METHOD` añadido con 5 valores globales (`company_id=NULL`): CASH (Efectivo), CARD (Tarjeta), TRANSFER (Transferencia Bancaria), STRIPE (Stripe / Pago Online), CREDIT (Crédito / Cuenta Corriente). Sirve el endpoint `GET /api/v1/enumerations?type=PAYMENT_METHOD`.
- **Sync de enums desde unified seed**: `unified_industrial_seed.py` Section 3 ahora llama `seed_enumerations(session)` en `master_data_db`, asegurando que todos los enums globales (incluyendo PAYMENT_METHOD) se sincronicen en ambas DBs (`dbname` y `master_data_db`).
- **Arquitectura**: `PAYMENT_METHOD` vive como enum dinámico en `enumerations` table — empresas pueden extender con métodos propios via `company_id` específico. El endpoint `GET /api/v1/enumerations?type=PAYMENT_METHOD` retorna globales + empresa.
- **Status**: ✅ COMPLETED — PAYMENT_METHOD disponible vía endpoint dinámico de enumeraciones.

### [2026-05-20] Phase 119: inventory_item_variants SSOT Migration + Point-in-Time Prices ✅
- **Table Migration**: `inventory_item_variants` recibida desde `inventory_db`. La tabla vive ahora en `master_data_db` (alembic `002_add_inventory_item_variants.py`). Permite JOIN ORM nativo en typeahead sin cruzar DBs.
- **ORM Model**: `master_app/models/item_variant.py` creado con `UniqueConstraint(company_id, internal_sku, mfg_part_number)`.
- **CRUD Variants** (`api/v1/endpoints/variants.py`): `GET /products/{id}/variants`, `POST /variants` (upsert + foto), `DELETE /variants/{id}`. Guard: `Security(require_scope(["master_data:read/write"]))`.
- **Repository Refactor** (`sqlalchemy_master_data_repository.py`): `get_products` y `get_product_by_sku` reescritos. ORM LEFT JOIN con `ItemVariant`. Cuando match por variante: `sku = variant.internal_sku`, nombre enriquecido `({brand} {mpn})`, precio = `variant.unit_price`. Anti-patrón `has_variants_table` eliminado.
- **Point-in-Time Price Endpoint**: `GET /prices/products/{id}/price-at?as_of=<datetime>` — soft-close query (`created_at <= as_of AND (valid_until IS NULL OR valid_until > as_of)`).
- **Typeahead verificado**: `?q=MPN-GAR` → `"Turbocharger Assembly (Garrett MPN-GAR-701)"` | price: `1200 MXN` ✅
- **Status**: ✅ COMPLETED — Variant SSOT en master_data_db. Code Graph 0 errores.

### [2026-05-17] Phase 109: Typeahead Consolidation & Transfer Price Seeding ✅
- **Typeahead API Fix**: Debugged and confirmed that the frontend was sending both POST and GET to `GET /api/v1/products?q=`. The GET endpoint is the correct one. Ensured the product search returns consolidated data including SKU, variant count, and base pricing.
- **Transfer Price Seeding (Inline)**: Eliminated the `setup_transfer_prices.py` subprocess dependency. Transfer prices (MXN enterprise pricing + USD cross-border pricing) for all 5 industrial products are now seeded directly in `unified_industrial_seed.py` via raw SQL, making the seed fully Docker-compatible.
- **Product Master Data**: Confirmed products are correctly seeded in `products` table with `product_type='GOODS'`, `status='ACTIVE'`, and proper multi-tenant fields.
- **Status**: ✅ COMPLETED — **Typeahead Unified & Pricing Seeded Inline**


- **Auditor Defense Remediation**: Re-engineered 63 endpoints to enforce strict `Security(require_scope, scopes=...)` validation, recovering from an accidental `git checkout` reversion and returning the service to a pristine 100% compliance rate.
- **Dynamic Method Scanning**: Implemented an automated injection script that distinguishes between HTTP verbs (GET vs POST/PUT/DELETE) to correctly map `master_data:read` or `master_data:write` permissions globally.
- **Status**: ✅ COMPLETED — **Security Enforcement Fully Restored**

### [2026-05-08] Phase 92: Industrial POS SKU Lookup & Variant Resolution ✅
- **Variant Search Logic**: Engineered a dual-stage lookup algorithm in `SQLAlchemyMasterDataRepository` that queries both primary `Product` and `InventoryItemVariant` tables simultaneously via SKU/Barcode.
- **Monolith Routing Alias**: Registered the `/api/v1/master-data/products/lookup/` route prefix within the unified monolith to ensure compatibility with legacy and mobile clients.
- **DB Injection Unification**: Re-wired the service to use `common.infrastructure.database.get_db`, resolving circular dependency issues during monolith startup.
- **POS API Support**: Activated the `/lookup/{code}` endpoint, returning standardized product metadata for real-time mobile checkout.
- **Status**: ✅ COMPLETED — **POS Lookup Motor Operational**

### [2026-05-01] Phase 78: Master Data Industrialization (SideDrawer Migration) ✅
- **UI Industrialization**: Refactored `WarehouseFormComponent` and `ConceptFormComponent` to the premium glassmorphic standard with sticky footers.
- **SideDrawer Standardization**: Unified all catalog modules under the `SideDrawerService` with strict `DrawerOptions` typing, resolving `TS2345` errors.
- **Template & Visibility Fixes**: Resolved `NG5002` syntax errors and corrected service visibility (`private` -> `public`) for template access.
- **Reactive Refresh**: Integrated `drawerService.refresh$` across all catalog components for seamless UI updates.
- **Status**: ✅ COMPLETED — **Master Data Domain Industrialized**

### [2026-05-01] Phase 77: Currency Service Integration ✅
- **Consolidación Core**: Migración exitosa de toda la lógica de `currency_service` al paquete `master_app`.
- **Industrial Rate Provider**: Implementación del cliente de **Banxico (FIX)** y **Frankfurter** con soporte para tokens de seguridad y fallback de mercados.
- **Unified Repository**: Integración de `SQLAlchemyCurrencyRepository` con soporte multi-tenant validado al 100% (Corrected: `company_id` filters in `get_by_id` and `verify_rate`).
- **Endpoint Registration**: Los endpoints `/currencies/*` ahora se sirven directamente desde el motor de Master Data.
- **Status**: ✅ COMPLETED — **Currency SSOT Stabilized**

### [2026-04-30] Phase 74: Subscription-Aware & Financial SSOT
- **SaaS Integrity**: El servicio ahora impone bloqueos de escritura para inquilinos en estado `RESTRICTED` o `UNPAID` mediante la sincronización con el `subscription_service`.
- **Definición Financiera (La Tríada)**: Consolidación de los tres pilares del valor: Landed Cost, CPP / WAC y Transfer Price como SSOT.
- **Sealed Price Support**: Inmutabilidad de precios en transferencias Inter-Company validada.

### [2026-04-21] Phase 67: Hierarchical Visibility & Global Catalogs
- **Tenant Context Resolution**: Validación del flujo get_current_tenant_context para extraer group_id del JWT, permitiendo filtros OR (company_id = X OR group_id = Y).
- **March 2026 - Structure of Holdings**: Introducción del modelo `BusinessGroup` para permitir catálogos compartidos jerárquicamente.
- **Data Repair**: Ejecución de script de mantenimiento para asignar group_id a registros huérfanos de Brands, Categories y UOMs.

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