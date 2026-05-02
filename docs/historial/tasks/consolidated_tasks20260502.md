# Consolidated Tasks - 2026-05-02

## Completadas
1. **Monolito**: Corrección del build context y recarga de contenedores (Docker `restart` en lugar de `up -d` pasivo) asegurando el enrutamiento exitoso de `/api/v1/events` (404 resuelto a 202 Accepted).
2. **Timezones**: Migración y corrección de columnas *Naive* (`DateTime`) a *Aware* (`DateTime(timezone=True)`) a nivel global (Outbox, Inventario, Notificaciones) para solucionar el conflicto `asyncpg` can't subtract offset-naive and offset-aware datetimes.
3. **Tickets Debouncing**: Implementación de prevención contra "tormentas de eventos" (`add_outbox_event`) validando ventanas de tiempo de 10 segundos para eventos idénticos usando SHA256 / limit. Inclusión de Suite completa de Unit Tests en `test_debouncing.py`.
4. **Tickets E2E**: Ejecución exitosa de flujo e2e. El Worker extrae los mensajes del Outbox de forma idónea, y la base de datos se mantiene consistente con el Escalation Watcher (tolerante a errores DNS dinámicos).
5. **Sync-Docs**: Ejecución de la auditoría de Código (Code Graph) logrando 100% de Cumplimiento en el Tickets Service.

## Pendientes (Inmediatas)
1. **Frontend Angular - Tickets**: 
   - Desarrollar modal `tickets-new-modal` (Signals + Glassmorphism).
   - Consumir el endpoint `/api/v1/tickets/config/constants`.
   - Lógica contextual por `ticket_type` (`MAINTENANCE` => `station_id` requerido).
   - Cierre dinámico del modal y renderizado de lista asíncrona.
2. **Frontend Angular - E2E**: Validar timezone de creación en Dashboard local y probar "Debouncing" de interfaz (doble clic).
3. **Estrategia Global de Timezones**: Formular un plan para normalizar el historial de los demás submódulos de Inventario / Producción / Financieros.
