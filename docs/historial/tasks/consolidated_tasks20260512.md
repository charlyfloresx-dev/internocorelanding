# Consolidated Tasks — 2026-05-12

## ✅ Completado

### Phase 104: Microservices Isolation & Gateway Stabilization

| # | Tarea | Estado |
|---|---|---|
| 1 | Configurar `version_table` únicas en Alembic para 7 servicios | ✅ |
| 2 | Crear `entrypoint.sh` industrial (Migrate→Seed→Serve) para todos los servicios | ✅ |
| 3 | Añadir Notification Service al `docker-compose.dev.yml` (puerto 8009) | ✅ |
| 4 | Añadir HCM Service al `docker-compose.dev.yml` (puerto 8004) | ✅ |
| 5 | Corregir Dockerfile HCM: `app` → `hcm_app` (Gold Standard) | ✅ |
| 6 | Resolver `ModuleNotFoundError: redis` en todos los servicios | ✅ |
| 7 | Eliminar import cruzado `notification_app` en `inventory_service` (2 archivos) | ✅ |
| 8 | Eliminar import cruzado `auth_app` en `notification_service` (1 archivo) | ✅ |
| 9 | Comentar upstream/location de `wms-service` en Nginx (no desplegado en dev) | ✅ |
| 10 | Añadir upstreams y locations de HCM y Notification en `nginx.conf` | ✅ |
| 11 | Actualizar Gateway `depends_on` para incluir los 7 servicios | ✅ |
| 12 | Crear `scripts/validate_ecosystem.ps1` (Ping Maestro) | ✅ |
| 13 | Integrar validator en `initialize-dev.md` y `sync-docs.md` workflows | ✅ |
| 14 | Añadir regla `CROSS_SERVICE_IMPORT_VIOLATION` al Code Graph | ✅ |
| 15 | Crear `backend/README.md` con Gold Standard de microservicios | ✅ |
| 16 | Añadir Sección 9 (Gold Standard) al `README.md` raíz | ✅ |
| 17 | Actualizar `infrastructure/README.md` rango de puertos (8001-8009) | ✅ |
| 18 | Ejecutar sync-docs completo y registrar en REPO_LOG | ✅ |

## ⏳ Pendiente (Backlog para siguiente sesión)

| # | Tarea | Prioridad |
|---|---|---|
| 1 | Inventory/HCM muestran `BadGateway` — revisar logs de arranque | ALTA |
| 2 | Ejecutar `full_auth_flow.py` exitosamente vía Gateway (puerto 8000) | ALTA |
| 3 | Desplegar Workers Asíncronos (Outbox, SLA) vía `docker-compose.workers.yml` | MEDIA |
| 4 | Cold Start Test: `docker compose down -v` + `up` desde cero | MEDIA |
| 5 | Implementar WMS Service y desbloquear su upstream en Nginx | BAJA |
