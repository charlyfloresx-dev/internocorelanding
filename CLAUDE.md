# InternoCore — Guía para Claude Code

**Proyecto:** InternoCore (nombre original: NexoSuite)  
**Arquitecto:** Carlos Flores Montoya  
**Estado:** Desarrollo activo — Phase 127 completada (2026-05-22). Pendiente despliegue cloud para clientes.  
**Stack:** FastAPI (Python 3.12+) · SQLAlchemy async · Alembic · PostgreSQL · Redis · Angular 19 · Flutter

---

## 1. Arquitectura General

**Modo actual:** Microservicios en Docker local orquestados por Nginx Gateway (puerto 8000).  
**Frontend:** Angular 19 Zoneless → `frontend/` → apunta al Nginx (8000).  
**Mobile:** Flutter INTERNO POS → `src/interno_billing_app/` → apunta al Nginx via IP de red local.  
**Proyectos en `src/`:** viatra_service, asset_manager, kiosk — son proyectos **alternos/personales**, NO parte del core. La única excepción es `src/interno_billing_app/`.

---

## 2. Servicios Activos en Docker

```
docker ps (estado actual)
```

| Contenedor | Puerto host | Imagen | DB |
|---|---|---|---|
| interno-gateway-dev | 8000 | nginx:alpine | — |
| interno-auth-dev | 8001 | interno-auth-service | dbname (shared) |
| interno-subscription-dev | 8002 | interno-subscription-service | subscription_db |
| interno-master-data-dev | 8003 | interno-master-data-service | master_data_db |
| interno-hcm-dev | 8004 | interno-hcm-service | hcm_db |
| interno-inventory-dev | 8006 | interno-inventory-service | inventory_db |
| interno-tickets-dev | 8008 | interno-tickets-service | dbname (shared) |
| interno-notification-dev | 8009 | interno-notification-service | dbname (shared) |
| interno-db-dev | 5433 | postgres:15-alpine | — |
| interno-redis-dev | 6379 | redis:7-alpine | — |

**NO desplegados:** wms_service (8007), mes_service — upstreams comentados en nginx.conf.

---

## 3. Variables de Entorno (`.env` raíz)

```env
CORE_ENV_MODE=development
CORE_DATABASE_URL=postgresql+asyncpg://user:internocore_db_pass_2026@localhost:5433/dbname
CORE_SECRET_KEY=ROTATED_SECRET_KEY_987654321_DEV
CORE_ALGORITHM=HS256
CORE_ACCESS_TOKEN_EXPIRE_MINUTES=1440          # 12 horas (turnos industriales)
CORE_ADMIN_MASTER_KEY=ROTATED_MASTER_KEY_GOD_MODE
CORE_HR_RFID_SALT=ROTATED_HR_RFID_SALT_7890
CORE_INTERNAL_API_KEY=ROTATED_INTERNAL_API_KEY_4567   # bypass rate limit
CORE_REDIS_URL=redis://interno-redis-dev:6379/0
CORE_STORAGE_BACKEND=local
CORE_STRIPE_SECRET_KEY=sk_test_...
CORE_STRIPE_WEBHOOK_SECRET=whsec_...
CORE_RESEND_API_KEY=re_...
CORE_BANXICO_TOKEN=...                         # tipo de cambio USD/MXN
```

Cada microservicio tiene su propio `.env` en su directorio. Contenedores usan `interno-db-dev:5432` (internamente), scripts host usan `localhost:5433`.

---

## 4. Reglas de Oro (respetar siempre)

### 4.1 Estructura Gold Standard
```
backend/<module>_service/
├── Dockerfile             # CMD ["/bin/sh", "/app/entrypoint.sh"]
├── entrypoint.sh          # Migrate → Seed → Serve
├── requirements.txt
├── alembic.ini
├── alembic/env.py         # CRÍTICO: version_table="alembic_version_<suffix>"
└── <module>_app/          # NUNCA usar carpeta genérica "app"
    ├── main.py
    ├── core/              # InternoSettings (hereda BaseSettings)
    ├── models/            # Heredan de MultiTenantBase
    ├── routers/ o api/
    ├── schemas/
    └── services/
```

### 4.2 Multi-tenancy — Muro de Hierro
- `company_id` SOLO del JWT verificado. Nunca del cliente (previene IDOR).
- Todos los modelos heredan `MultiTenantBase`. NO heredar `AuditBase` además (es redundante, ya está incluido).
- `common/infrastructure/database.py` tiene `do_orm_execute` + `with_loader_criteria` + checkout listener para RLS de Postgres.

### 4.3 Tipos financieros — Float Prohibido
- **PROHIBIDO `float`** en models/schemas/domain. Usar `Decimal` (`Numeric(18,4)`) o Value Object `Money`.
- Excepción: coordenadas geográficas (`lat`/`lng`).

### 4.4 Comunicación inter-servicio
- Microservicios NO importan módulos de otros. Solo HTTP (`httpx`) o raw SQL `text()` para tablas compartidas.

### 4.5 Ledger de inventario — inmutable
- `inventory_transactions` es append-only. Prohibido UPDATE/DELETE.

### 4.6 CQRS
- GET endpoints NO hacen `db.commit()` ni `db.add()`.
- Command Handlers que mutan DEBEN usar `begin_nested()`.

### 4.7 Sin float, sin root pollution, sin eliminar archivos LOG/SPECS.md.

---

## 5. Dominio de Inventario (foco actual)

### Modelos clave (`inventory_service/inventory_app/models/`)

**`InventoryDocument`** — cabecera del documento
```python
class DocumentStatus(Enum): DRAFT / PROCESSED / CANCELLED

class InventoryDocument(MultiTenantBase):
    folio: str                    # "OUT-ABC123" — único
    document_type: str            # IN / OUT / TRANSFER / ICT_OUT / ICT_IN
    status: DocumentStatus        # DRAFT → PROCESSED al confirmar
    origin_name: str              # nombre UI (Industrial Mimesis)
    destination_name: str
    total_items: int
    total_amount: Money           # composite(Decimal, currency)
    external_reference: str       # UUID del doc como idempotency key
    pending_financial_valuation: bool  # True si se creó sin precio → widget Finanzas
    audit_notes: str              # JSON de warnings del agente pre-vuelo
```

**`InventoryTransaction`** — línea del ledger (inmutable)
```python
class InventoryTransaction(MultiTenantBase):
    product_id, warehouse_id
    transaction_type: TransactionType   # IN / OUT / TRANSFER / etc.
    quantity_change: Decimal            # negativo para salidas
    previous_balance, new_balance: Decimal
    reference_id: UUID                  # → document_id
```

**`InventoryLevel`** — saldo actual por producto/almacén
```python
class InventoryLevel(MultiTenantBase):
    warehouse_id, product_id, uom_id
    quantity: Decimal
    reserved_quantity: Decimal
    available_quantity = quantity - reserved_quantity   # @property SSOT
    wac: Money          # Costo Promedio Ponderado
    last_price: Money
    replacement_price: Money
```

**`ItemVariant`** — variantes por proveedor (para scan de variante)
```python
class ItemVariant(MultiTenantBase):
    __tablename__ = "inventory_item_variants"
    product_id: UUID          # → products.id en master_data
    internal_sku: str         # SKU interno
    brand: str                # Bosch, Denso, Garrett, Brembo, etc.
    mfg_part_number: str      # MPN — código escaneable
    unit_price: Decimal
    weight, volume: Decimal
    is_preferred: bool
    # UQ: (company_id, internal_sku, mfg_part_number)
```

### Flujo de venta móvil (pantalla de ventas actual)

```
Scan código → GET /products/lookup/{code} (master_data)
           → resuelve Product o ItemVariant por SKU/MPN
           → retorna precio (Pricing Onion Layers)

Cambio de cliente → seleccionar partner_id → ajusta precio por PriceAgreement

Confirmar documento:
  1. Crear InventoryDocument (DRAFT)
  2. Por cada ítem: MovementEntity con quantity negativa (OUT)
     → SQLAlchemyInventoryRepository.record_movement()
  3. SET status = PROCESSED → commit atómico
```

**BUG CONOCIDO (Phase 109):** `GET /products/{id}/variants` retorna 403 para rol `collaborator`. Fix pendiente: agregar `inventory:read` al scope mapping del colaborador.

### Scripts de flujo de validación (`inventory_service/scripts/flows/`)

| Script | Qué valida |
|---|---|
| `flow_1_entry.py` | Entrada (IN) 150 unidades |
| `flow_2_exit.py` | Salida (OUT) 20 unidades (quantity negativa) |
| `flow_3_internal_transfer.py` | Traspaso interno (requiere 2 usuarios — SoD) |
| `flow_4_ict_enterprise_to_logistics.py` | ICT entre empresas del mismo grupo |
| `flow_5_ict_binational.py` | ICT binacional MX/US |
| `flow_6_purchase_variants.py` | Compra masiva de 15 variantes (1,500 uds) |
| `flow_7_putaway.py` | Put-away (DOCK → RACK) |
| `flow_8_adjustments.py` | Ajustes de inventario |
| `flow_9_relocation.py` | Relocalización entre ubicaciones |
| `seed_variants.py` | Seed de variantes industriales (ECM, Turbo, Brake, Injectors, Dampers) |

---

## 6. Arquitectura de Precios (`docs/specs/06_PRICES_AND_FISCAL_CATALOGS.md`)

### Regla Soft-Close (crítica)
Un precio en `product_prices` **NUNCA se modifica ni borra**:
1. Se sella el registro anterior: `valid_until = NOW()`
2. Se inserta nuevo registro: `valid_until = NULL`
3. Precio vigente = registro con `valid_until IS NULL`

### Pricing Onion Layers (resolución en checkout)
```
1. PriceAgreement (contrato B2B por partner_id)  ← precio más específico
2. ProductPrice por warehouse_id
3. ProductPrice por price_list_index asignado
4. ProductPrice lista pública
```

### Point-in-Time (reimprimir documentos históricos)
```sql
WHERE created_at <= :document_date
  AND (valid_until IS NULL OR valid_until > :document_date)
```
**Implementado (Phase 119):** `GET /prices/products/{id}/price-at?as_of=<datetime>` en `master_data_service`. `MasterDataClient.get_product_price_at_date()` en `inventory_service`.

### Fiscal
- **SAT (MX):** `sat_product_code` (8 dígitos)
- **HTS (US):** `hts_code` (10 dígitos) para transferencias internacionales
- Precios en DB son **NETOS** — IVA (8%/16%) o Sales Tax se calcula en checkout

---

## 7. Seguridad

| Mecanismo | Detalle |
|---|---|
| **Handshake T1/T2** | Login → `selection_token` + empresas → `select-company` → JWT final |
| **JWT claims** | `sub`, `company_id`, `group_id`, `roles`, `modules`, `readonly`, `scopes` |
| **JWT lifespan** | 12h (`CORE_ACCESS_TOKEN_EXPIRE_MINUTES=1440`) |
| **Rate Limiting** | SlowAPI + Redis. Bypass: `X-Internal-Secret` o `X-Admin-Master-Key`. Key: user → tenant → IP. Global: 2000/h, 100/min |
| **Session Heartbeat** | Redis blocklist `blacklist:{user_id}` + cache local 5min |
| **bcrypt** | work_factor=12 |
| **Subscription Guard** | Bloquea mutaciones si `PAST_DUE`. GET/HEAD/OPTIONS libres |
| **RLS Postgres** | `SET LOCAL app.current_tenant` en cada conexión del pool |
| **God Mode** | `X-Admin-Master-Key` — bypass rate limit + scope `*` |

---

## 8. Resumen por Microservicio

### auth_service (8001)
- SSOT de identidad. T1/T2 Handshake. Refresh token con hash en BD.
- `collaborator_login_command.py`: login industrial vía RFID/PIN (T1 bypass).
- `delegate-selection`: genera `selection_token` para QR mobile provisioning.
- Tokens: `access` (12h), `refresh`, `selection` (short-lived).

### subscription_service (8002)
- Planes, entitlements, estado de suscripción. Integración Stripe.
- `PAST_DUE` → readonly. `UNPAID` → paywall total.
- Endpoint: `/internal/entitlements/{company_id}` para cross-service.

### master_data_service (8003)
- SSOT de productos, UOM, categorías, precios, partners.
- **Currency SSOT:** Banxico (FIX) + Frankfurter como fallback. Endpoint `/currencies/`.
- **Lookup POS:** `GET /api/v1/products/lookup/{code}` — busca en `products` Y `inventory_item_variants` simultáneamente por SKU/MPN.
- **Typeahead:** `GET /api/v1/products?q=` (solo GET, no POST).
- Precios: 10 listas por empresa. Soft-Close pattern. Composite `Money` VO.
- `PriceAgreement`: contratos B2B con `valid_until` (Soft-Close & Insert).

### hcm_service (8004) — ex hr_service
- Colaboradores, RFID/PIN, departamentos, certificaciones.
- DB propia: `hcm_db` (separada de dbname).
- `CORE_HCM_RFID_SALT` para hashing de tarjetas RFID.
- **Vinculación:** `user_id` en `Collaborator` conecta con auth_service.
- **`Department` model** (Phase 118): Entidad `Department` con CRUD `/departments`. Habilita routing de tickets a área de planta.
- **`audit_logs`** en `hcm_db`: creada (Phase 118) — `AuditService` funcional.
- **`internal_id_pattern`** en `hr_tenant_configs`: columna añadida (Phase 118).

### inventory_service (8006)
- Kardex inmutable. `inventory_transactions`, `inventory_levels`, `inventory_documents`.
- `InventoryDocument`: DRAFT → PROCESSED. Folio único, `external_reference` como idempotency key.
- `ItemVariant`: tabla `inventory_item_variants` — vive en `master_data_db` (SSOT desde Phase 119). Endpoints de variantes en inventory_service son proxies HTTP.
- Density Guard: valida capacidad de ubicación antes de cada movimiento IN.
- Bulk load: `POST /api/v1/inventory/bulk-load` con `X-Internal-Secret` bypass.

### tickets_service (8008)
- Incidencias, SLA, Triple Identity (Internal/Plant/External).
- Outbox pattern para notificaciones async.
- Debouncing de eventos (ventana 10s).

### notification_service (8009)
- Email (Resend), WhatsApp (Twilio Sandbox), webhooks HMAC-SHA256.
- Dispatch matrix: HIGH priority → fuerza IN_APP + EMAIL + PUSH.

### wms_service (8007) — NO desplegado en dev
- Warehouse management, ubicaciones, despacho.
- `InventoryClient` HTTP para comunicarse con inventory_service.

### mes_service — NO desplegado en dev
- OEE, producción en piso, turnos, Andon.
- `MISSING_DOMAIN_LOGIC_WARNING` conocido en Code Graph.

---

## 9. Frontend (Angular 19 Zoneless)

**Directorio:** `frontend/`  
**Dev server:** `cd frontend && npm run start` → `http://localhost:4200`  
**Estructura:** `src/app/` → `core/` · `modules/` · `shared/`  
**Testing:** Playwright E2E (`npx playwright test`)

Características:
- Zoneless (máxima eficiencia CPU/batería para tablets industriales)
- Signals reactivos (Angular 19)
- `multi-tenant.interceptor.ts`: inyecta `Authorization` + `X-Company-ID` en cada request
- `resilience.interceptor.ts`: exponential backoff (2s, 4s, 8s) para errores de red
- `X-Client-Request-ID` (UUID v4) en mutaciones → idempotency
- Sistema de i18n ES/EN con `TranslatePipe` (pure: false)
- Paywall reactivo con Signals (`isReadOnly`, `isUnpaid`)

---

## 10. Mobile (INTERNO POS — Flutter)

**Directorio:** `src/interno_billing_app/`  
**Dispositivo de prueba:** Moto g04s (device ID: `adb-ZL7324NDXD-e2sm8j._adb-tls-connect._tcp`)

```powershell
# Correr en dispositivo físico (desde directorio interno_billing_app)
cd interno_billing_app; flutter pub get; flutter run -d adb-ZL7324NDXD-e2sm8j._adb-tls-connect._tcp --debug
```

**Configuración de API:** Login Screen → URL `http://<IP_LOCAL>:8000` (Nginx Gateway)  
**AVD emulador:** usar `10.0.2.2` en lugar de `localhost` para conectar al host.

Características clave:
- QR provisioning: escanea QR del portal web → hereda `baseUrl + accessToken + companyId + warehouseId`
- Handshake T1/T2 propio: `selection_token` → `/select-company` → JWT final en el device
- `ResilienceInterceptor`: exponential backoff + `X-Idempotency-Key` por request
- Scanner: `MobileScanner` se pruning del árbol widget al abrir el carrito (fix hardware BLASTBufferQueue Moto g04s)
- `ScannerBloc` maneja estado del carrito

**Flujo actual de ventas (foco Phase 112):**
1. Escanear código → busca producto en `GET /api/v1/products/lookup/{code}`
2. Resolución de precio por Pricing Onion Layers (incluye PriceAgreement si hay `partner_id`)
3. Cambio de cliente: `PartnerSearchModal` → selecciona partner → actualiza precios B2B
4. Carrito: lista de ítems con nombre + código (doble línea)
5. Confirmar → `POST /api/v1/pos/checkout` → crea `InventoryDocument` + movimientos OUT atómicos

---

## 11. Code Graph Auditor

```powershell
# Desde raíz del repo
python backend/scripts/generate_code_graph.py

# Comparar modelos vs DB live (requiere DB corriendo)
python backend/scripts/generate_code_graph.py --audit-schema
```

**Cuándo correr:** siempre en `sync-docs`, y al detectar gaps arquitectónicos durante desarrollo.  
**Criterio de éxito:** 0 CRITICAL. Exit code 1 si hay CRITICALs.

| Invariante | Sev | Detecta |
|---|---|---|
| `CROSS_SERVICE_IMPORT_VIOLATION` | CRITICAL | import directo entre servicios |
| `MURO_DE_HIERRO_VIOLATION` | CRITICAL | database.py sin do_orm_execute |
| `PRIMITIVE_FLOAT_VIOLATION` | CRITICAL | float en models/schemas |
| `CQRS_QUERY_VIOLATION` | CRITICAL | GET con commit/add |
| `CQRS_ATOMICITY_VIOLATION` | CRITICAL | Handler sin begin_nested() |
| `SCHEMA_MODEL_COUPLING` | CRITICAL | Schema importa ORM models |
| `RESILIENCE_VIOLATION` | CRITICAL | engine sin pool_pre_ping=True |
| `AWS_BUDGET_VIOLATION` | CRITICAL | ALB en código |
| `AWS_READINESS_VIOLATION` | CRITICAL | Config sin BaseSettings / localhost hardcodeado |
| `MISSING_DENSITY_GUARD` | CRITICAL | entrada stock sin validación capacidad |
| `ENV_ACCESS_VIOLATION` | WARNING | os.getenv fuera de core/config |
| `MISSING_SCOPE_VALIDATION` | WARNING | endpoint sin require_scope |
| `MISSING_TENANT_FILTER` | WARNING | query sin company_id |
| `SUBSCRIPTION_AWARENESS_WARNING` | WARNING | write sin chequeo de estado |

---

## 12. Workflows Activos

| Workflow | Archivo | Uso |
|---|---|---|
| `initialize-dev` | `.agent/workflows/initialize-dev.md` | Levantar stack desde cero |
| `hard-reset` | `.agent/workflows/hard-reset.md` | Reset nuclear (borra volúmenes + imágenes) |
| `sync-docs` | `.agent/workflows/sync-docs.md` | Cierre de fase: Code Graph + REPO_LOG + commit |
| `run-mobile-app` | `.agent/workflows/run-mobile-app.md` | Deploy en Moto g04s físico |

```powershell
# Levantar stack completo
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Migrar todos los servicios
powershell -ExecutionPolicy Bypass -File infrastructure/docker/migrate_all.ps1

# Seed industrial (requiere stack corriendo)
docker run --rm --network docker_interno-network -v ${PWD}/backend:/backend -w /backend `
  --env-file .env interno-auth-service:latest python scripts/unified_industrial_seed.py

# Validar ecosistema
powershell -ExecutionPolicy Bypass -File scripts/validate_ecosystem.ps1

# Code Graph
python backend/scripts/generate_code_graph.py
```

---

## 13. Deuda Técnica Activa (al 2026-05-27)

| Prioridad | Item |
|---|---|
| ~~CRÍTICA~~ | ~~**MES** `WorkOrder` model↔handler mismatch~~ — ✅ RESUELTO Phase 149 |
| ~~CRÍTICA~~ | ~~**MES/Inventory** `BOM.__repr__` referencia `parent_item_code`~~ — ✅ RESUELTO Phase 149 |
| ALTA | **MES** WorkOrder Patrón Documento+Líneas — `WorkOrderLine` faltante, `WorkOrder` no hereda `WorkOrderBase`. Spec: `docs/specs/MES_WORKORDER_DOCUMENT_PATTERN.md` |
| ALTA | **MES** Backflush de materiales — se resuelve con `WorkOrderLine(MATERIAL_INPUT)` (bloqueado por tarea anterior) |
| ALTA | **MES** `WorkOrder.manufactured_quantity` nunca se actualiza — se resuelve con `WorkOrderLine(ACTUAL_OUTPUT)` (bloqueado por tarea anterior) |
| ALTA | **MES** Dockerfile usa paths obsoletos (`app` en vez de `mes_app`) — servicio no desplegable. Corregir COPY + CMD + agregar a docker-compose + nginx |
| ALTA | **MES** `mes_db` vacía (0 tablas) — `alembic upgrade head` nunca corrió. Bloqueado por tarea de Dockerfile |
| ALTA | **MES** Tests de integración WorkOrder contra `mes_db` real — bloqueados por las dos tareas anteriores |
| ALTA | Validar `POST /api/v1/pos/checkout` end-to-end con flows de antigravity |
| MEDIA | **MES** Transición automática de WO status: DRAFT → IN_PROGRESS → COMPLETED |
| MEDIA | Rate limit por endpoint faltante en WMS, MES, HR, Subscription |
| MEDIA | `default_tax_rate` Planta US debería ser 0.0 (actualmente 0.16) |
| MEDIA | Precio según partner seleccionado en typeahead (PriceAgreement context en `GET /products/?q=`) |
| MEDIA | **Mobile** Revisar app en AVD (Pixel 7 API 34) — theme dark/light + flujo completo de venta |
| MEDIA | **HCM** CRUD de Departamentos en Angular (configuración de áreas por empresa) |
| BAJA | **HCM** `JobPosition` catálogo propio (actualmente solo `job_title: str`) |
| BAJA | **HCM** `shift_id` en Collaborator → bridge HCM↔MES |
| BAJA | **HCM** jerarquía 3 niveles: `manager_id` + `director_id` (actualmente solo `supervisor_id`) |
| BAJA | WMS no desplegado en dev stack |
| BAJA | Offline buffer SQLite para mobile en zonas sin conectividad |
| BAJA | Self-Service Stripe Checkout para tenants UNPAID |
| BAJA | **MES** `routing.py` vacío — `Rout` model sin implementar (archivo existe, cuerpo vacío). FK `wo_type` en WorkOrder también falta |
| BAJA | **MES** `Planning` + `Facility` + `ProductionArea` models faltantes (warehouse scheduling, planta física) |
| BAJA | **MES** `ProductionRunWorkOrder` pivot (many-to-many ProductionRun↔WorkOrder) faltante |
| BAJA | **MES** Enums faltantes en `core/enums.py`: `WOType` (7 valores), `ProdIssueType` (8 valores), `IssueType` (6 valores) |
| BAJA | **MES** `RunMetricsSnapshot` incompleto — faltan: OE, TEP, FirstPassYield, OverTime, Improvement |
| BAJA | **MES** `HourlyProductionSnapshot` incompleto — faltan: std_time_seconds, paid_hours, employees_qty, issues_count (para calcular GainedHrs/Attainment/Eficiency) |
| BAJA | **MES** `Tracking` incompleto — faltan: alias, target, comment, start/close/reject user_ids, reject_time |
| BAJA | **MES** Endpoints faltantes: `GET /resources/{code}/graphic` (algoritmo ~120L), `GET /dashboard` OEE, bulk Excel (WO, Planning, StandardTimes) |

---

## 14. Documentación de Referencia

| Documento | Ruta |
|---|---|
| Arquitectura + puertos + protocolo | `README.md` |
| Historial de fases (1–111) | `REPO_LOG.md` |
| Tareas diarias | `docs/historial/tasks/consolidated_tasksYYYYMMDD.md` |
| Implementación por sesión | `docs/historial/implementation/master_implementation_historyYYYYMMDD.md` |
| Precios y catálogos fiscales | `docs/specs/06_PRICES_AND_FISCAL_CATALOGS.md` |
| MES WorkOrder Documento+Líneas | `docs/specs/MES_WORKORDER_DOCUMENT_PATTERN.md` |
| Specs OpenAPI | `docs/specs/*.json` (auth, inventory, master_data, tickets, wms, subscription, mes) |
| Log por servicio | `backend/<svc>/SERVICE_LOG.md` |
| Contexto de negocio | `docs/historial/backend/<svc>/CONTEXTO.md` |
| Auditor estático | `backend/scripts/generate_code_graph.py` |
| Flujos de validación inventario | `backend/inventory_service/scripts/flows/` |
