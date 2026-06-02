# Tareas — 2026-06-02 (Phase 161)

## Completadas

| # | Tarea | Servicio | Resultado |
|---|---|---|---|
| 1 | Corregir restricciones de claves primarias y foráneas (`WorkOrder`, `Resource`, `ProductionArea`, `Facility`) en tests de asignación | mes_service | ✅ |
| 2 | Eliminar colisiones de claves duplicadas de órdenes usando nombres únicos dinámicos en los tests de integración | mes_service | ✅ |
| 3 | Inyectar bypass del middleware de autenticación (God Mode) y mockear `get_current_active_user` para pruebas de integración locales | mes_service | ✅ |
| 4 | Resolver deprecación de Pydantic `class Config` -> `ConfigDict` en el esquema de asignación | mes_service | ✅ |
| 5 | Ejecutar suite completa de integración de asignaciones (`test_production_assignment.py`) con 100% de éxito | mes_service | ✅ |
| 6 | Sincronización de documentación y verificación del estado de cumplimiento del Code Graph del repositorio | docs | ✅ |

## Pendientes carryover

| Prioridad | Item |
|---|---|
| ALTA | Resolver las 8 advertencias de `NAIVE_DATETIME_VIOLATION` en `auth_service`, `inventory_service`, `tickets_service` y `wms_service` detectadas por el Code Graph |
| ALTA | **Phase 156 B.1**: `ResourceConfigComponent` Angular — CRUD visual de celdas/máquinas |
| ALTA | **Phase 156 B.2**: `ShiftConfigComponent` Angular con ShiftBreak inline |
| MEDIA | **Phase 156 D.1**: `WorkOrderFormComponent` + `DailyPlanningComponent` |
| MEDIA | `Rout` model MES — BOM + Rutas de Producción |
| MEDIA | Rate limit por endpoint en WMS, MES, HCM, Subscription |
