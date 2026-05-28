# Tareas — 2026-05-28 (Phase 150)

## Completadas

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | Reescribir Dockerfile: `app` → `mes_app` | mes_service | ✅ |
| 2 | Crear `entrypoint.sh` (migrate→seed→serve) | mes_service | ✅ |
| 3 | Añadir mes-service a `docker-compose.dev.yml` | infra | ✅ |
| 4 | Descomentar `/api/v1/mes` en `nginx.conf` | infra | ✅ |
| 5 | Añadir `interno-mes-dev` a `migrate_all.ps1` | infra | ✅ |
| 6 | `WorkOrder` model: `wo_type`, `rout_id`, relationship `lines` | mes_service | ✅ |
| 7 | Crear `WorkOrderLine` model (Patrón Documento+Líneas) | mes_service | ✅ |
| 8 | Migration `008_wo_doc_pattern`: enums, tenant_id, `mes_work_order_lines` | mes_service | ✅ |
| 9 | `WorkOrderHandler`: BOM explode + MATERIAL_INPUT + PLANNED_OUTPUT lines | mes_service | ✅ |
| 10 | `GET /work-orders/{order_number}/lines` endpoint | mes_service | ✅ |
| 11 | Build + deploy `interno-mes-dev`, alembic upgrade head | infra | ✅ |
| 12 | 17 integration tests contra mes_db real | mes_service | ✅ |
| 13 | Fix `WorkOrderLine.work_order_id` faltaba `ForeignKey` | mes_service | ✅ |
| 14 | Migrar tests SQLite → PostgreSQL (JSONB incompatibilidad) | mes_service | ✅ |
| 15 | `CLAUDE.md` deuda técnica actualizada | docs | ✅ |
| 16 | `REPO_LOG.md` + `SERVICE_LOG.md` actualizados | docs | ✅ |

## Pendientes carryover

| Prioridad | Item |
|---|---|
| ALTA | `WorkOrder.manufactured_quantity` → hook en ScannerService |
| ALTA | Validar `POST /api/v1/pos/checkout` end-to-end |
| MEDIA | MES: transición automática DRAFT → IN_PROGRESS → COMPLETED |
| MEDIA | Rate limit por endpoint en MES |
| BAJA | `mes_app.schemas.planning` PydanticUserError (campo name clash) |
| BAJA | `test_mes_core.py` xfail: services requieren repo injection — actualizar cuando se estabilice API |
