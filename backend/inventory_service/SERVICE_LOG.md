# Service Log — Inventory Service

## 🕒 Última Actividad (2026-05-24) — Phase 131
**Phase 131: payment_method como campo propio en inventory_documents** ✅
- **Migration 003** (`alembic/versions/003_add_payment_method_to_documents.py`): Columna `payment_method VARCHAR(20) NULL` añadida a `inventory_documents`. Down: `op.drop_column`. Chain: `002_drop_inventory_item_variants` → `003_add_payment_method_to_documents`.
- **`InventoryDocument` model** (`models/document.py`): `payment_method: Mapped[Optional[str]]` — almacena la key del enum dinámico `PAYMENT_METHOD` (CASH, CARD, TRANSFER, etc.). NULL para entradas/ajustes.
- **`InventoryDocumentCreate` schema** (`schemas/inventory.py`): `payment_method: Optional[str] = None` añadido.
- **`create_document` endpoint** (`api/v1/endpoints/transactions.py`): `doc_entity` incluye `"payment_method": doc.payment_method`.
- **`create_inventory_document` repository** (`infrastructure/repositories/sqlalchemy_inventory_repository.py`): Constructor de `InventoryDocument` recibe `payment_method=document_entity.get("payment_method")`.
- **Status**: ✅ COMPLETED — `payment_method` es un campo de primera clase. Workaround `_buildNotes()` eliminado.

## 🕒 Última Actividad (2026-05-21)
**Phase 121 Fase 1: Structural Housekeeping** ✅
- **`inventory_app/main.py`**: Eliminado bloque de imports duplicado (líneas 72-88 re-importaban los mismos 4 routers ya declarados en línea 14). Eliminados `CORSMiddleware`, `Base`, `engine` (no usados). `from fastapi import FastAPI, Request, status` consolidado.
- **`scripts/scratch/`** (NUEVO directorio): 20 scripts de debug/utilidad temporal movidos desde la raíz del servicio. Directorio añadido a `.gitignore`. La raíz queda limpia para producción.
- **`models/__init__.py`**: `InventoryLocation` verificada como ya correctamente expuesta. Sin cambios requeridos.
- **`requirements.txt`**: Dependencias verificadas como ya pinneadas. Sin cambios requeridos.
- **Status**: ✅ COMPLETED — Servicio listo para despliegue en producción sin deuda estructural.

**Phase 120: Iron Wall Fix — company_id from JWT only** ✅
- **`api/v1/endpoints/inventory.py`** (10 endpoints): Eliminado `x_company_id: UUID = Header(...)` de `/movements`, `/reconcile`, `/reserve`, `/release`, `/transfers/dispatch`, `/transfers/receive`, `/stock/{warehouse_id}/{product_id}`, `/stock`, `/audit-export`, `/cycle-count`. Reemplazado por `token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))`. El `company_id` proviene exclusivamente del JWT verificado — el cliente no puede suplantar tenant.
- **`api/v1/endpoints/dashboard.py`** (9 endpoints): Mismo patrón aplicado a `/summary`, `/movements`, `/stock`, `/force-release`, `/reports/kardex`, `/reports/valuation`, `/reports/abc`, `/mission-control`, `/consolidated`.
- **`/bulk-load`** conserva `X-Internal-Secret` — endpoint de uso inter-servicio exclusivamente.
- **Impacto de seguridad:** Eliminada vulnerabilidad IDOR que permitía a cualquier tenant acceder a datos de otro tenant.

## 🕒 Última Actividad (2026-05-20)
**Phase 119: inventory_item_variants Moved to master_data_db + Document Reprint Endpoint** ✅
- **Table Drop** (`alembic/versions/002_drop_inventory_item_variants.py`): `inventory_item_variants` eliminada de `inventory_db`. La tabla es ahora SSOT de `master_data_service`. Downgrade = `pass` (migración one-way intencional).
- **Variant endpoints → HTTP Proxy** (`api/v1/endpoints/variants.py`): Los 3 endpoints (GET/POST/DELETE) ahora hacen proxy HTTP a `master_data_service` via `httpx`, propagando `Authorization` y `X-Company-ID`. No tocan BD local.
- **Document Reprint endpoint** (`api/v1/endpoints/documents.py`): `GET /api/v1/inventory/documents/{folio}` — retorna cabecera + líneas con precios al momento de creación. Usa `MasterDataClient.get_product_price_at_date()` para soft-close lookup.
- **MasterDataClient** ampliado con `get_product_price_at_date(product_id, company_id, as_of, list_index)`.
- **Seed cleanup**: `scripts/seed.py` — import `ItemVariant` y seeding de variantes eliminados; check `InventoryLevel` cambiado a unique-constraint lookup `(company_id, warehouse_id, product_id)`; `inventory_item_variants` removida del `--wipe` list.
- **Status**: ✅ COMPLETED — inventory_service libre de `inventory_item_variants`. Code Graph 0 errores.

## 🕒 Última Actividad (2026-05-18)
**Phase 114: Mobile Offline-First Sync & UUID Architecture Enforcement** ✅
- **UUID Determinism Enforced**: Removed flexible UUID resolution adapter for `concept_id` in `inventory.py` service and `transactions.py` API endpoints. The Backend now strictly enforces system UUIDs instead of resolving string codes (like `'ENT-PUR'`).
- **Audit & Validation**: Verified the end-to-end industrial transaction flow using testing scripts that dynamically fetch concepts, proving strict schema compliance without 500 errors.
- **Status**: ✅ COMPLETED — Inventory API strict contract preserved.

## 🕒 Última Actividad (2026-05-18)
**Phase 113: Security Hardening — BOLA Fix & Price Enumeration** ✅
- **`pos.py` — BOLA eliminado (C-3)**: (1) Validación de `warehouse_id` contra `token.company_id` antes de procesar cualquier ítem — devuelve `ERR_WAREHOUSE_NOT_OWNED` 403. (2) Query a `products` ahora incluye `AND company_id = :cid` — los raw `text()` bypasean el `do_orm_execute` ORM interceptor, por lo que el filtro debe estar en el SQL explícitamente.
- **`pos.py` — Price enumeration eliminado (H-1)**: El 400 de `PRICE_MISMATCH` ya no incluye `resolved_price` ni SKU en el detail — solo `ERR_PRICE_MISMATCH` genérico.
- **`pos.py` — `RequirePermission("pos.checkout")` aplicado (H-3)**: Reemplaza el `SubscriptionGuard` raw. Garantiza que solo usuarios con slug `pos.checkout` en JWT puedan procesar ventas.
- **`pos.py` — Float prohibido corregido**: `float(sale.total_amount)` → `str(sale.total_amount)` en el documento creado.
- **Status**: ✅ COMPLETED — POS checkout multi-tenant seguro.

## 🕒 Última Actividad (2026-05-18)
**Phase 112: pos.py Bug Fixes & RequirePermission Guard** ✅
- **`pos.py` — Import `Decimal` faltante**: Agregado `from decimal import Decimal`. Sin este import, cualquier checkout con precio resuelto desde DB lanzaba `NameError` al evaluar `abs(Decimal(str(resolved_price)) - item.unit_price)`.
- **`pos.py` — Cantidad negativa en OUT**: Corregido `quantity_change=item.quantity` → `quantity_change=-item.quantity`. El repositorio calcula `new_balance = stock.quantity + movement.quantity_change` — sin signo negativo el stock aumentaba en cada venta.
- **`RequirePermission` guard disponible**: `backend/common/security/require_permission.py` exportado desde `common.security`. Listo para aplicar en endpoints de aprobación de documentos, bulk-load y auditoría forense.
- **Status**: ✅ COMPLETED — POS checkout funcional. Guard RBAC disponible para endpoints de alta sensibilidad.

## 🕒 Última Actividad (2026-05-17)
**Phase 109: Seed Unification, Variants API & Docker-Compatible Seeding** ✅
- **Variants API Endpoint**: Implemented `GET /api/v1/inventory/products/{product_id}/variants` to return item variants (brand, MPN, unit price, weight) for a given product. Used by both the Angular frontend typeahead and the Flutter mobile scanner.
- **Unified Seed Consolidation (Docker-Compatible)**: Eliminated ALL `subprocess.run()` calls from `unified_industrial_seed.py`. All seeding now uses inline SQL via the inventory_db session:
  - **15 Item Variants** (5 products × 3 brands) seeded via `INSERT INTO inventory_item_variants ... ON CONFLICT DO NOTHING`.
  - **35 WMS Locations** (3 virtual zones + LOC-AUDIT-01 + LOC-TIJ-RECV-01 + 24 rack + 6 picking) seeded inline.
  - **Shadow Movement Concepts** mirrored from master_data for cross-db independence.
  - **Customs Pedimentos & Movements** for 3 companies seeded inline with location normalization.
- **Known Issue**: `GET /products/{id}/variants` returning 403 for `collaborator` role — scope mapping needs `inventory:read` added to allowed scopes.

## 🕒 Última Actividad (2026-05-16)
**Industrial Ecosystem Cold-Start & Seed Hardening (Phase 108)**
- **Isolated Seeding Engine**: Refactored `unified_industrial_seed.py` to trigger sub-seeds via `subprocess.run`. This provides total environmental isolation, ensuring that the Inventory DB connection is correctly initialized without interference from the Auth DB context.
- **Cold-Start Certification**: Verified the successful re-population of shadow warehouses and product variants into the `inventory_db` following a nuclear infrastructure prune.
- **Relational Integrity**: Confirmed that seeded inventory items (ECM-600) correctly reference the global company IDs established in the Auth layer.

## 🕒 Última Actividad (2026-05-16)
**Inventory Baseline & Schema Stabilization (Phase 107)**
- **Migration Flattening**: Consolidated all legacy migrations into a single `000_inventory_baseline.py` to ensure a clean, idempotent bootstrap.
- **Audit & Multi-Tenancy Hardening**: Injected missing audit and multitenant columns into all 15 core inventory tables, ensuring consistency with the global Code Knowledge Graph.
- **Deterministic Seeding**: Refactored the local `seed.py` to target default development companies automatically, facilitating cold-starts without manual configuration.
- **Infrastructure Cleanup**: Deprecated `migrate_schema.py` and updated `entrypoint.sh` for an Alembic-first strategy.

## 🕒 Última Actividad (2026-05-13)
**Resilience Stress-Test & Idempotency (Phase 101)**
- **Bulk Load Idempotency**: Integrated `X-Idempotency-Key` (UUIDv4) support in `bulk-load` endpoint. Batches are now registered in `idempotency_keys` table to prevent duplication during network retries.
- **Chaos Test Certification**: Successfully processed 1,000,000 records under a DB "Kill Switch" scenario. The service resumed operations instantly after DB restoration thanks to `pool_pre_ping=True`.
- **Bypass Verification**: Verified that `X-Internal-Secret` correctly bypasses the rate limiter for high-volume ingestion.
**AWS S3 Neutralization & Recipe Serialization (Phase 98)**
- **Cloud Storage Decommissioning**: Verified the deletion of residual logging buckets in S3 and confirmed $0.00 cost status for the service.
- **Storage Strategy Transition**: Formally established the `LocalStorageProvider` as the primary engine for the Unified Monolith mode.
- **ADN Extraction**: Exported service-specific network topology and IAM roles to the centralized `backup_configs/` repository.

## 🕒 Última Actividad (2026-05-10)
**Entitlement Hardening & Scope-based Guard (Phase 95)**
- **Entitlement Seeding**: Synchronized `unified_industrial_seed.py` to ensure `inventory_core` is present in the `Entitlement` matrix for all primary tenants. This resolves the `403 Forbidden` errors during high-volume POS checkouts.
- **Scope Bypass Architecture**: Refactored the transversal `SubscriptionGuard` to prioritize the `*` (super-admin) scope. Users with administrative entitlements can now bypass module-level lockdowns, ensuring environment continuity during recovery or provisioning.
- **Transactional Audit**: Verified that the POS checkout loop correctly resolves and logs the inventory movement even under strict subscription enforcement.

## 🕒 Última Actividad (2026-04-30)

## 🕒 Última Actividad (2026-03-15)
**Sealed Price (Precio Sellado) & Inter-Company Governance**
- **Sealed Price Pattern**: Aprobación inmutable del patrón de transferencias Inter-Company: el precio de venta de la Empresa A se convierte en el costo de compra de la Empresa B al momento del despacho, sin cambios posteriores.
- **Financial Triad**: Consolidación del SSOT Financiero regido por la tríada: Landed Cost, CPP / WAC y Transfer Price.
- **Kardex Inmutability**: El ledger ahora garantiza que cualquier movimiento financiero sea inalterable una vez sellado.

## 🕒 Última Actividad (2026-04-27)
**Forensic Audit & Financial Mapping (Fase 71)**

## 🕒 Última Actividad (2026-04-21)
**Hierarchical Inventory Visibility (Fase 67)**
- **Shadow Warehouse Mapping**: Alineación de almacenes logísticos con la jerarquía de grupos para visibilidad cross-company.
- **Tenant Context Consistency**: Verificada la propagación de X-Company-ID y group_id en las transacciones de inventario.

\n## 🕒 Última Actividad (2026-04-15)\n**Industrial Data Simulation (Fase 53 Completada)**\n- Ejecución de Bypass Directa a DB (SQLAlchemy Core) en modo simulación masiva.\n- Generadas +180 transacciones de inventario simulando 15 días consecutivos para validar Frontend rendering.\n- Alineación estricta de la estructura en vivo (`inventory_transactions`) y mitigación de NotNullViolationErrors por evolución de esquemas (`available_quantity`, `is_transit`) en crudo, evadiendo la API.\n\n## 🕒 Actividad Previa (2026-04-15)\n**Outbound Shipping & Audit Export (Completada)**\n1. **Audit Sheet Export (Compliance Anexo 24)**:\n   - Implementado endpoint `/warehouses/{id}/audit-export` para la generación de hojas de auditoría física en CSV.\n   - Soportado encoding UTF-8-BOM y mapeo de campos de cumplimiento fiscal (SKU, Ubicación, Pedimento).\n2. **Dispatch Validation Bridge**:\n   - Expuesto soporte para la recepción de credenciales de operador durante el despacho de transferencias.\n   - Preparada la estructura para validación sincrónica contra el microservicio de HR (Fase 50).\n\n## 🕒 Última Actividad (2026-04-15)\n**Integridad Industrial y "The Density Guard" (Completada)**\n\n1. **The Density Guard (Control de Capacidad)**:\n   - Implementado modelo `InventoryLocation` para definir capacidad física (`max_capacity`) por Rack/Bin.\n   - Añadida validación en tiempo real en `InventoryTransactionService` que bloquea movimientos si exceden la capacidad (Ocupación = Suma de saldos FIFO).\n   - Expuesto endpoint `/locations/{code}/density` para monitoreo preventivo desde Handhelds.\n2. **Optimización de Búsqueda (Registry Cache)**:\n   - Creado endpoint `/search/products/quick-catalog` para hidratación instantánea del frontend ($O(1)$ lookup).\n   - Implementada limpieza de escaneos (método `getNumber` rescatado de legacy) para eliminar sufijos basura.\n3. **Módulo de Put-Away (Handheld)**:\n   - Desarrollada interfaz industrial para re-ubicación de mercancía (DOCK -> RACK).\n   - Implementado flujo de "3 Scans" con retroalimentación auditiva (Beeps) y validación de ubicación.\n   - Vinculación automática de `pedimento_id` para asegurar el cumplimiento del Anexo 24 en traslados internos.\n4. **Estabilización de Reportes Anexo 24**:\n   - Refactorizada la capa de respuesta de `/customs/balances` para evitar el doble envoltorio (double-wrap) de `ApiResponse`.\n\n## 🕒 Última Actividad (2026-04-15)\n**Escalabilidad Industrial y Cumplimiento Anexo 24 (Completada)**\n\n1. **Paginación y Búsqueda en Auditoría**:\n   - Modificado `IInventoryRepository` y `SQLAlchemyInventoryRepository` para soportar `limit`, `offset` y `query`.\n   - Implementado cálculo de `total_count` mediante subconsultas para reportes de cumplimiento.\n   - Optimizado el endpoint `/balances` para retornar metadata de paginación industrial.\n2. **Estabilización de Dominio**:\n   - Unificadas implementaciones de `get_customs_balances` eliminando shims y placeholders.\n   - Reforzada la lógica de cálculo de días de vencimiento (Risk Aging) con soporte para zonas horarias.\n**Enriquecimiento Forense de Documentos (Completada)**\n\n1. **Resolución de Nombres de Terceros (Partners)**:\n   - Modificado `InventoryTransactionService` y el endpoint `/documents` para realizar búsquedas activas en `master-data-service` durante la creación del documento.\n   - Si el campo `external_entity` contiene un UUID, el servicio ahora lo resuelve a un nombre comercial (ej. "COCA-COLA FEMSA MÉXICO") antes de persistirlo.\n   - Implementado patrón de resiliencia: Si el servicio externo falla, se mantiene el ID original para evitar pérdida de datos.\n2. **Infraestructura de comunicación (IMasterDataClient)**:\n   - Agregada capacidad `get_partner` al cliente interno para facilitar la resolución de nombres en otros módulos.\n   - Reforzada la resolución de nombres de almacenes físicos.\n\n\n## 🕒 Última Actividad (2026-04-09)\n**Depuración de Flujos y Enriquecimiento de Catálogos (Completada)**\n\n1. **Correcciones en Flujos de Scripts**:\n   - **`flow_2_exit.py`**: Corregido el signo de la cantidad a negativo (`-20.0`) para asegurar que el balance de stock se descuente correctamente en el ledger.\n   - **`flow_3_internal_transfer.py`**: Implementada la Segregación de Funciones (SoD). El flujo ahora utiliza un segundo usuario (`USER_B_ID`) para la recepción, cumpliendo con la validación de seguridad `ERR_SELF_RECEIPT_NOT_ALLOWED` re-activada en el handler.\n2. **Carga de Datos Maestros (Seeding)**:\n   - Creado `scripts/flows/seed_variants.py`.\n   - Registrados 5 Números de Parte industriales (ECM, Turbo, Brake Disc, Injectors, Dampers) con un total de 15 variantes (Bosch, Denso, Garrett, Brembo, etc.).\n   - Asegurada la compatibilidad con `MultiTenantBase` y el esquema de auditoría de `inventory_db`.\n3. **Validación Técnica**:\n   - Ejecución exitosa de los 6 flujos tras las correcciones.\n   - Validación de conectividad local a la DB a través del puerto mapeado `5433`.\n   - Confirmada la persistencia de movimientos (`inventory_movements`) y documentos (`inventory_documents`) con trazabilidad completa.\n\n## 🕒 Última Actividad (2026-04-09 12:30 PM)\n**Flujo de Aprovisionamiento Masivo (Completado)**\n1. **`flow_6_purchase_variants.py`**:\n   - Implementada lógica de compra masiva. Registradas 100 unidades de cada una de las 15 variantes (1,500 unidades totales) en el almacén principal de Tijuana.\n   - Generado folio `PURCHASE-` vinculado a una Orden de Compra externa simulada (`PO-`).\n   - Verificado el cálculo de `total_amount` en USD en la cabecera del documento.\n   - Activado el escalonamiento de capas FIFO (`available_quantity`) para futuras salidas.\n