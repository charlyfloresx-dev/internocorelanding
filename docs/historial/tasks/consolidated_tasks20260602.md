# Tareas Consolidadas — 2026-06-02 (Phases 161 + 167–171)

---

## Phase 171 — Unified Resource Monitor + Bug Fixes ✅

| # | Tarea | Resultado |
|---|---|---|
| 1 | Unified resource-monitor: tabs Producción / Personal en una sola pantalla | ✅ |
| 2 | production_run_id optional en badge endpoint — auto-resolve por resource_code | ✅ |
| 3 | `GET /mes/orders/types` movido antes de `/{order_number}` (FastAPI route ordering 404 fix) | ✅ |
| 4 | Migración 013+014 aplicada al DB corriendo (employees_qty, group_id columns) | ✅ |
| 5 | Eliminados hardcodes `hcm-service:8000`, `inventory-service:8000`, `localhost:8000` → `settings.int_*` | ✅ |
| 6 | `CORE_HCM_SERVICE_URL=http://interno-hcm-dev:8000` en docker-compose.dev.yml | ✅ |
| 7 | HCMClient paths corregidos: `/collaborators/*` → `/staff/*` | ✅ |
| 8 | `import logging; logger` añadido a labor_badge.py (NameError silencioso) | ✅ |
| 9 | `production_run_id=dest_run.id` en Labor creation (era request.production_run_id = None) | ✅ |
| 10 | `ALTER COLUMN updated_at DROP NOT NULL` en mes_collaborator_badges + mes_hourly_labor_snapshots | ✅ |
| 11 | `.trim()` en processScan() frontend + `.strip()` en backend para `\n` del QR decoder | ✅ |
| 12 | html5-qrcode: mover `#reader-monitor` fuera de `@if` → siempre en DOM (race condition fix con OnPush) | ✅ |
| 13 | Migración 015: añadir columnas MultiTenantBase faltantes (group_id, updated_by, deleted_at, transaction_id) | ✅ |
| 14 | **E2E verificado**: Carlos Ramírez `003709A` → 200 SUCCESS action=TRANSFER, 53ms latency | ✅ |

---

# Tareas Consolidadas — 2026-06-02 (Phase 161 + Phase 167 + Phase 168 + Phase 169)

---

## Phase 170 — Shop Floor Badge Auth & Headcount UI ✅

| # | Tarea | Archivo | Resultado |
|---|---|---|---|
| 1 | `CollaboratorBadge` model — soft FK, badge_raw_value indexado, degraded mode name | `models/collaborator_badge.py` | ✅ |
| 2 | `POST /clock-in-by-badge` — CLOCK_IN/TRANSFER auto/ALREADY_CLOCKED_IN | `api/v1/endpoints/labor_badge.py` | ✅ |
| 3 | Badge CRUD admin (GET/POST/PATCH/DELETE /badges) | `api/v1/endpoints/labor_badge.py` | ✅ |
| 4 | Migración `014_collaborator_badges.py` | `alembic/versions/` | ✅ |
| 5 | `LaborService` Angular con signals (headcount + clockInByBadge + badgeCRUD) | `core/services/labor.service.ts` | ✅ |
| 6 | `ShopFloorComponent` — HID scanner listener, debounce 1.5s, offline queue, headcount panel, gráfica horaria | `modules/production/floor/` | ✅ |
| 7 | Ruta `/production/floor/:resourceId` | `app.routes.ts` | ✅ |
| 8 | Fix `onboarding.component.ts` — `${{ }}` template literal + `row[col]` unknown | frontend | ✅ |

---

## Phase 169 — Headcount Tracking & Labor Density ✅

| # | Tarea | Archivo | Resultado |
|---|---|---|---|
| 1 | `LaborCategory` enum (ACTIVE/TRANSFER/PERMIT/BREAK/OVERTIME) + `LaborType.category` | `models/labor.py` | ✅ |
| 2 | `HourlyLaborSnapshot` read model CQRS con estado subdividido | `models/hourly_labor_snapshot.py` | ✅ |
| 3 | Extender `HourlyProductionSnapshot` con `employees_qty`, `paid_hrs_total`, `gained_hrs_total` | `models/production_snapshot.py` | ✅ |
| 4 | `LaborDensityService.materialize_range()` con roll-over fix (recalcula todas las horas del intervalo) | `services/labor_density_service.py` | ✅ |
| 5 | Integrar `LaborDensityService` en `clock_in` y `clock_out` | `api/v1/endpoints/labor.py` | ✅ |
| 6 | `POST /mes/labor/transfer` — atómico con Orphan Transfer rule (valida destino antes de mutar) | `api/v1/endpoints/labor.py` | ✅ |
| 7 | `GET /mes/labor/headcount/{resource_id}` — foto actual subdividida | `api/v1/endpoints/labor.py` | ✅ |
| 8 | `GET /mes/labor/headcount-history/{resource_id}?date=` — serie horaria O(1) | `api/v1/endpoints/labor.py` | ✅ |
| 9 | Migración DDL `013_labor_headcount.py` | `alembic/versions/` | ✅ |
| 10 | Registro `HourlyLaborSnapshot` en `models/__init__.py` + `get_labor_density_service` en `dependencies.py` | infra | ✅ |

---

## Phase 168 — Bulk Import Onboarding Wizard ✅

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | `POST /api/v1/products/bulk` — UOM/categoría ILIKE, idempotente por SKU, siembra ProductPrice lista-1 | master_data | ✅ |
| 2 | `POST /api/v1/partners/bulk` — mapeo rfc→tax_id, city→address, idempotente por code | master_data | ✅ |
| 3 | `POST /api/v1/hcm/collaborators/bulk` — JSON (vs CSV /bulk-upload), resuelve depto ILIKE, hash RFID+PIN, upsert por internal_id | hcm_service | ✅ |
| 4 | `onboarding.service.ts` — payload keys corregidas (products/partners/collaborators) | frontend | ✅ |

---

# Tareas Consolidadas — 2026-06-02 (Phase 161 + Phase 167)

## Completadas

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | Corregir restricciones de claves primarias y foráneas (`WorkOrder`, `Resource`, `ProductionArea`, `Facility`) en tests de asignación | mes_service | ✅ |
| 2 | Eliminar colisiones de claves duplicadas de órdenes usando nombres únicos dinámicos en los tests de integración | mes_service | ✅ |
| 3 | Inyectar bypass del middleware de autenticación (God Mode) y mockear `get_current_active_user` para pruebas de integración locales | mes_service | ✅ |
| 4 | Resolver deprecación de Pydantic `class Config` -> `ConfigDict` en el esquema de asignación | mes_service | ✅ |
| 5 | Ejecutar suite completa de integración de asignaciones (`test_production_assignment.py`) con 100% de éxito | mes_service | ✅ |
| 6 | Sincronización de documentación y verificación del estado de cumplimiento del Code Graph del repositorio | docs | ✅ |

---

## Phase 167 — Landing v2 + Onboarding Wizard ✅

### Landing Page (`src/landing/`)
- `index.html`: motion@latest CDN, dashboard mockup animado (KPIs live, barras OEE, feed RFID), tech stack bar (FastAPI/Angular/PostgreSQL/Docker/Flutter/Redis), mobile hamburger menu, scroll progress bar
- `style.css`: grid bg hero, glassmorphism, shimmer CTA, terminal audit stream mejorado, responsive mobile nav, `.cert-badge`, `.arch-link`, `.dashboard-mockup`
- `app.js`: Motion inView stagger (feature-cards, pricing, skills), counters animados (-$4.76M, 100%), live KPI ticker, typewriter audit stream (9 logs rotativos)
- **Sección Architect**: datos reales del CV — Safran Aerospace, DJO/Enovis, Outset Medical, SMK Electronics. Énfasis en manufactura médica/aeroespacial con rutas complejas, trazabilidad FDA Clase II/III, AS9100, ISO 9001. LinkedIn + email reales.
- `plans.html`: tabla con filas Trazabilidad + Validación Rutas AS9100/FDA, precios en headers de columna, mobile menu, motion CDN, CTA con i18n
- `ticket-access.html`: eliminados `alert()`/`prompt()` → toast animado + formulario comentario inline con spinner; `escapeHtml()` XSS; grid bg; branding footer
- `locales/es.json` + `en.json`: `footer.home`, `plans_page.cta_*`, `plans_table.traceability/routing`, `architect.*` con DJO/Enovis y énfasis médico/aeroespacial
- `package.json`: documenta `motion@latest` como CDN dependency

### Onboarding Angular (`frontend/`)
- `onboarding.service.ts` (nuevo): API methods por paso + `downloadCsv` (UTF-8 BOM) + `parseCsv` robusto (maneja comillas)
- `onboarding.component.ts` (reescrito completo): 8 pasos con Signals Angular 19
  | Step | Contenido |
  |---|---|
  | 1 Empresa | nombre, RFC, sector, país, moneda, timezone, IVA, norma |
  | 2 Plan | tarjetas Operativo $45 / Industrial $350 / Enterprise $550+ |
  | 3 Catálogo | tags categorías + drag-drop CSV productos con preview 5 filas |
  | 4 Partners | drag-drop CSV clientes/proveedores con preview |
  | 5 Almacén | nombre, código, tipo (PHYSICAL/VIRTUAL/TRANSIT), dirección |
  | 6 Personal | drag-drop CSV colaboradores con RFID/PIN con preview |
  | 7 MES/Planta | facility + toggle Omitir + lista auto-creados (3 turnos, áreas) |
  | 8 Alertas | email, IN-APP, WhatsApp/Twilio creds + toggle Omitir |
- CSV templates inline con datos reales (Cojinete SKF 6205, maquiladora ACME, EMP001 Producción)
- `CLAUDE.md`: deuda ALTA "Landing Onboarding" agregada

## Pendientes activos

| Prioridad | Item |
|---|---|
| ALTA | Landing Onboarding: validar wizard contra stack real + endpoints bulk backend (products/bulk, partners/bulk, hcm/collaborators/bulk) |
| ALTA | POS checkout E2E: `flow_pos_checkout.py` listo, nunca ejecutado |
| MEDIA | NAIVE_DATETIME 8 archivos (auth/inventory/tickets/wms) |
| MEDIA | PriceAgreement typeahead `GET /products?q=` sin partner_id |
| MEDIA | Mobile AVD Pixel 7 API 34 |
| MEDIA | Domain purity RTR: `log_rotation_event()` retorna ORM model |
| BAJA | @limiter.limit() por-endpoint WMS/MES/HCM/Subscription |
| BAJA | RTR AWS WAF + observabilidad, GAP-5 ADR, GAP-6 |
| BAJA | HCM JobPosition catálogo, WMS no desplegado, MES routing.py vacío |

## Code Graph — 2026-06-02 Phase 167
- **0 CRITICALs** ✅
- 8 WARNINGs NAIVE_DATETIME (deuda conocida, sin impacto en prod actual)
- Endpoints internos: tickets 400 (no 200) ✅ · subscription 403 ✅
