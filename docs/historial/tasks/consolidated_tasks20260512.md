# InternoCore: Consolidated Tasks - 2026-05-12

## Contexto
Phase 99: Muro de Hierro (Rate Limiting) — COMPLETADA.
Phase 100: Big Bang (1M Records Stress Test) — COMPLETADA.

## Tareas Completadas ✅
1.  **Integración de Redis en el Monolito**: Migrada dependencia de Redis a `docker-compose.monolith.yml`.
2.  **SlowAPIMiddleware Activo**: Rate limiting centralizado con `slowapi` interceptando ráfagas de tráfico.
3.  **Multi-layer Key**: Validada identificación de cuotas por Usuario > Tenant > IP.
4.  **AttributeError Fix**: Corregido exception handler de `slowapi` para manejar errores de conexión a Redis.
5.  **Aislamiento Multi-tenant**: Superadas pruebas de inyección masiva (429 para Tenant_A sin afectar Tenant_B).
6.  **Control de Log-Spam**: Verificado que los errores 429 no saturan logs.
7.  **Bypass Administrativo**: Implementado `X-Internal-Secret` y `X-Admin-Master-Key` en `multi_layer_key_func` para exentar procesos de migración/carga masiva.
8.  **Endpoint `/bulk-load`**: Creado en `inventory_service` con inserción atómica vía `executemany` y mapeo de Enum.
9.  **CORS Cleanup**: Eliminados duplicados lowercase de cabeceras. Solo PascalCase.
10. **BOM Fix**: Resuelto problema de codificación UTF-8 BOM en `.env` causado por PowerShell.
11. **Hard Reset Workflow**: Actualizado con paso de sanitización BOM.
12. **Big Bang Loader v2**: Reescrito con pre-flight check, batch 1k, concurrencia 3, timeout 120s.
13. **Nuclear Docker Cleanup**: Limpieza total de imágenes y volúmenes; poda de redes residuales (`bridge`, `host`, `none` verificados).
14. **Ejecución Exitosa del Big Bang**: Inyectados 1,000,000 de registros Kardex en 39.9s (25k rec/s).
15. **Backend Transaction Mapping Fix**: Corregido mapeo `ADJUST` -> `ADJUSTMENT` en el endpoint `/bulk-load`.

## Pendientes ⏳
1.  **Robustez de Enums**: Implementar `IF NOT EXISTS` o migraciones Alembic para evitar `UniqueViolationError` en arranque concurrente (detectado en Phase 100).
2.  **Ajuste de Cuotas por Tier**: Definir límites diferenciados en Redis por plan de suscripción.
3.  **Monitoreo en Tiempo Real**: Integrar contadores de Rate Limit en Dashboard Forense del Frontend.
4.  **Auditoría de Integridad**: Ejecutar `audit_inventory_integrity.py` para validar el Ledger de 1M.
