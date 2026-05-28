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

## Phase 153 — Kiosk Company Binding + ID Pattern + Light Theme (2026-05-28)

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | Migration `internal_id_pattern` en `companies` | auth_service | ✅ |
| 2 | Validación `re.fullmatch()` en `collaborator_login_command` Step 0 | auth_service | ✅ |
| 3 | `PATCH /companies/my/id-pattern` endpoint | auth_service | ✅ |
| 4 | HCM hotfix: `department.name` en `collaborator_verify_service` | hcm_service | ✅ |
| 5 | Flutter: `_handleAutoLogin` guarda `kiosk_company_id` desde QR | mobile | ✅ |
| 6 | Flutter: `_buildKioskCompanyBadge` estado sin provisionar con instrucciones | mobile | ✅ |
| 7 | Flutter: light theme `receipts_screen.dart` (reescritura completa) | mobile | ✅ |
| 8 | Flutter: light theme `sales_screen.dart` (bottom sheet + modals) | mobile | ✅ |
| 9 | `kiosk_auth_flow.py` — 4-test suite (RFID, PIN, company-bound, pattern) | auth_service | ✅ |
| 10 | SERVICE_LOG auth + hcm actualizados | docs | ✅ |

## Phase 154 — Análisis Architecture Resource Monitor (2026-05-28)

| # | Tarea | Resultado |
|---|---|---|
| 1 | Análisis `ResourceMonitorComponent` — 100% mock, 0 HTTP calls | ✅ |
| 2 | Análisis legacy `Interno.Production` — 12 modelos + 7 controllers | ✅ |
| 3 | Decisión: `Resource : Warehouse` → soft FK en Python (Iron Wall) | ✅ |
| 4 | Plan de 4 partes en `PENDIENTES_INDUSTRIAL_CORE.md` con checkboxes | ✅ |
| 5 | Phase 153 + 154 añadidos a `REPO_LOG.md` | ✅ |

## Phase 155 — HCM — Industrial Identity & Cross-Border Eligibility Hardening (2026-05-28)

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | Añadir campos `assigned_plant`, `shift`, `global_entry_id` a Collaborator ORM, entity, schemas | hcm_service | ✅ |
| 2 | Añadir `cross_border_expiry_threshold_days` a `HrTenantConfig` model | hcm_service | ✅ |
| 3 | Refactorizar `_calculate_eligibility` para usar el threshold del tenant y validar Visa + CDL + Med + (Sentry OR Global Entry) | hcm_service | ✅ |
| 4 | Crear migración Alembic `005_add_plant_shift_global_entry` y aplicar | hcm_service | ✅ |
| 5 | Sincronizar script de siembra unificada `unified_industrial_seed.py` | scripts | ✅ |
| 6 | Ejecutar el seed y validar la siembra de colaboradores binacionales | hcm_service | ✅ |
| 7 | Actualizar documentación del repositorio (CLAUDE.md, REPO_LOG, SERVICE_LOG) | docs | ✅ |

## Pendientes carryover

| Prioridad | Item |
|---|---|
| ALTA | **Phase 154 Parte 1**: `Facility` + `ProductionArea` + `Resource` + migration + seed + CRUD |
| ALTA | **Phase 154 Parte 2**: `GET /graphic` algoritmo hora×hora + `active-workorder` + `planned-workorders` |
| ALTA | **Phase 154 Parte 3**: `ResourceService` Angular + desconectar mock + `:code` param |
| ALTA | Validar `POST /api/v1/pos/checkout` end-to-end |
| MEDIA | Rate limit por endpoint en WMS, MES, HCM, Subscription |
| MEDIA | Precio según partner seleccionado en SalesScreen (PriceAgreement en lookup) |
| BAJA | `mes_app.schemas.planning` PydanticUserError (campo name clash) |
| BAJA | `test_mes_core.py` xfail: services requieren repo injection |
