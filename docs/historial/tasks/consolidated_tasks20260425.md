# Consolidated Tasks — 2026-04-25

Bitácora operativa del día. Captura el backlog superado y los pendientes activos para el Sprint 2.

---

## ✅ Completado — Sprint 1: Asset Manager Service (Interno Assets CRM)

### Infraestructura y Proyecto
- [x] Crear directorio `backend/asset_manager_service` con estructura Clean Architecture completa.
- [x] Inicializar `README.md` y `REPO_LOG.md` del nuevo microservicio.
- [x] Crear `requirements.txt`, `Dockerfile` y `alembic.ini` siguiendo el estándar del monolito.
- [x] Agregar `asset_manager_db` a `backend/scripts/init-multiple-databases.sh`.
- [x] Agregar servicio `asset-manager-service` al `docker-compose.yml` (puerto `8011:8006`).

### Data Schema (Modelos SQLAlchemy)
- [x] Modelo `Opportunity`: Clave catastral, coords, propietario RPPC, métricas financieras (`adeudo_total`, `valor_m2_zona`, `estimated_market_value`, `gastos_legales`, `risk_buffer_percentage`, `projected_roi`), flags (`is_investment_opportunity`, `needs_manual_data`), pipeline Kanban (`status` enum), `days_in_pipeline` (calculado).
- [x] Modelo `ZoneConfig`: Valor de mercado por colonia con lógica de "aprendizaje" (sistema persiste el VM cuando el usuario lo ingresa manualmente).
- [x] Modelo `OpportunityAuditLog`: Bitácora de cambios en el pipeline Kanban (quién, qué y cuándo).
- [x] Alembic `env.py` async configurado.
- [x] Migración inicial `0001_initial_schema.py` con las 3 tablas e índices.

### Financial Engine (Application Layer)
- [x] `OpportunityEvaluator`: Motor financiero puro. Fórmula: `ROI = VM - (PA + adeudo + gastos + VM * risk_buffer)`. Umbral de oportunidad: 20% de adeudo/VM. Sin estado, determinista, testeable de forma aislada.
- [x] `OpportunityOrchestrator`: Orquestador que recibe el payload del `/full-report`, resuelve el VM (override → ZoneConfig → None), evalúa financieramente y hace upsert con AuditLog.

### Repository Layer (Infrastructure)
- [x] `OpportunityRepository`: Listado filtrable por `status`, `needs_manual_data`, `min_roi`, `created_by` (scope personal del Scout). Kanban status update con AuditLog. Recálculo automático de ROI al recibir datos manuales.
- [x] Compliance Code Graph: Anotación `bypass_tenant` documentada en los métodos del repositorio (CRM personal, scope por `created_by`, no `company_id`).

### API Endpoints (5 rutas)
- [x] `POST /api/v1/opportunities/evaluate` — Ingesta de datos del full-report.
- [x] `GET /api/v1/opportunities` — Dashboard Kanban con filtros (`?status=`, `?needs_data=`, `?min_roi=`, `?opportunities_only=`).
- [x] `GET /api/v1/opportunities/{cve_cat}` — Detalle de predio.
- [x] `PATCH /api/v1/opportunities/{cve_cat}/status` — Movimiento Kanban.
- [x] `PATCH /api/v1/opportunities/{cve_cat}/data` — Completar datos manuales (recalcula ROI automáticamente).
- [x] `GET /api/v1/opportunities/zones/config` — Catálogo de colonias con VM.

### Integración Async (BackgroundTask)
- [x] `gis_validator.py` modificado: El endpoint `/full-report` ahora lanza `_propagate_to_asset_manager` como BackgroundTask (fire-and-forget). **No bloquea la respuesta del mapa a Indiana.**

### Testing
- [x] `test_opportunity_evaluator.py`: 8 escenarios unitarios (Oro, umbral 20%, ROI negativo, risk_buffer, datos faltantes, compra directa, threshold constant).
- [x] `test_rppc_integration.py`: 4 tests de integración (retry de variaciones PK-020-119, validación Unidad C ≠ Jorge Alejandro, fallback por Localidad, formato de claves).

### Bugs Corregidos (Pre-existentes detectados durante el sprint)
- [x] **`master_data_service/Dockerfile`**: COPY path incorrecto `app/` → `master_app/` (la carpeta real del módulo).
- [x] **`master_data_service/entrypoint.sh`**: CMD uvicorn `app.main:app` → `master_app.main:app`.

### Sync-Docs (Workflow)
- [x] Code Graph Audit: **100% CLEAN — TOTAL ERRORS: 0** (14 microservicios).
- [x] Docker build `asset-manager-service`: ✅ Exitoso.
- [x] `alembic upgrade head` — Ejecutado (vía stamp head + shadow fix).
- [x] Tests unitarios `pytest test_opportunity_evaluator.py -v` — Ejecutados.
- [ ] Test integración RPPC `pytest test_rppc_integration.py -v -s`.
- [x] Git commit de cierre de fase.

---

## 🔄 Pendiente — Sprint 2

### Validación del Pipeline Completo
- [ ] `docker exec asset-manager-service-api alembic upgrade head`
- [ ] `pytest tests/test_opportunity_evaluator.py -v` (sin conectividad)
- [ ] `pytest tests/test_rppc_integration.py -v -s` (con conectividad)
- [ ] Flujo E2E: `POST /full-report` → BackgroundTask → `GET /v1/opportunities`

### Frontend Integration (Indiana Map-Tool)
- [ ] Actualizar respuesta de `/full-report` en el frontend: el campo cambia de `clave` → `cve_cat`.
- [ ] Agregar botón "Guardar como Oportunidad" en el popup del mapa que llame a `PATCH /{cve_cat}/data` con el `valor_m2_zona` ingresado manualmente.
- [ ] Dashboard Kanban (vista de lista de oportunidades con ROI).

### ZoneConfig Seeding
- [ ] Crear seed inicial con colonias de alta actividad en Tijuana (Presidentes, Otay, Centro) y sus valores de m² estimados.
