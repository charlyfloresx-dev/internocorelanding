# Tareas — 2026-05-29 (Phase 156)

## Phase 156-A — MES Cold-Start: Seed de Configuración

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | Migration 010: corregir `UQ(code)` global → `UQ(company_id, code)` en `mes_shifts` | mes_service | ✅ |
| 2 | `scripts/seed_mes_config.py`: Facility + ProductionArea + Resource + Shift + ShiftBreak + StandardTime | mes_service | ✅ |
| 3 | IDs determinísticos `uuid5("mes156.<tipo>.<company_id>.<code>")` para idempotencia | mes_service | ✅ |
| 4 | Seed cubre 3 empresas (ENTERPRISE, LOGISTICS_MX, LOGISTICS_US) | mes_service | ✅ |
| 5 | `scripts/seed.py` actualizado para llamar `seed_mes_config()` | mes_service | ✅ |
| 6 | Parámetro `db_url` en `seed_mes_config()` para tests (evita colisión con `.env` raíz) | mes_service | ✅ |
| 7 | 19 integration tests para seed — 19/19 pasando | mes_service | ✅ |
| 8 | Migración aplicada en `interno-mes-dev`, seed ejecutado automáticamente | infra | ✅ |
| 9 | Verificado via psql: 3 facilities, 9 areas, 12 resources, 9 shifts, 18 breaks, 15 stdtimes | infra | ✅ |

## Phase 156-C — Shift REST Endpoints CRUD

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | `GET /` mejorado: devuelve `breaks[]` embebidos + tiempos como `"HH:MM"` | mes_service | ✅ |
| 2 | `POST /` crear turno con validación código duplicado → 409 | mes_service | ✅ |
| 3 | `GET /{shift_id}` con breaks embebidos | mes_service | ✅ |
| 4 | `PATCH /{shift_id}` partial update (nombre, tiempos, is_active, break_minutes) | mes_service | ✅ |
| 5 | `DELETE /{shift_id}` soft-delete (is_active=False) | mes_service | ✅ |
| 6 | `GET /{shift_id}/breaks` lista breaks ordenados por hora | mes_service | ✅ |
| 7 | `POST /{shift_id}/breaks` crear break | mes_service | ✅ |
| 8 | `DELETE /{shift_id}/breaks/{break_id}` hard-delete | mes_service | ✅ |
| 9 | `_parse_time()` helper convierte "HH:MM" → `datetime.time` | mes_service | ✅ |
| 10 | 13 integration tests Shift CRUD — 13/13 pasando | mes_service | ✅ |
| 11 | Build y redeploy `interno-mes-dev` con endpoints nuevos | infra | ✅ |
| 12 | Endpoint verificado en vivo: GET `/api/v1/mes/shifts/` retorna turnos con breaks | infra | ✅ |

## Totales de tests MES tras Phase 156

| Suite | Tests |
|---|---|
| `test_manufactured_quantity.py` | 9 |
| `test_resource_expanded.py` | 18 |
| `test_resource_graphic.py` | 11 |
| `test_seed_mes_config.py` | 19 |
| `test_shift_crud.py` | 13 |
| `test_work_order_lines.py` | 17 |
| **TOTAL** | **87** |

## Pendientes carryover

| Prioridad | Item |
|---|---|
| ALTA | **Phase 156 B.1**: `ResourceConfigComponent` Angular — CRUD visual de celdas/máquinas |
| ALTA | **Phase 156 B.2**: `ShiftConfigComponent` Angular con ShiftBreak inline |
| ALTA | Validar `POST /api/v1/pos/checkout` end-to-end |
| MEDIA | **Phase 156 D.1**: `WorkOrderFormComponent` + `DailyPlanningComponent` |
| MEDIA | `Rout` model MES — BOM + Rutas de Producción |
| MEDIA | Rate limit por endpoint en WMS, MES, HCM, Subscription |
| MEDIA | Precio según partner seleccionado en SalesScreen (PriceAgreement en lookup) |
| BAJA | `mes_app.schemas.planning` PydanticUserError (campo name clash) |
