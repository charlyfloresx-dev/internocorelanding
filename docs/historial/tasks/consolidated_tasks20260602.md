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
