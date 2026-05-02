# Master Implementation History - 2026-05-02

## Objetivo: Industrialización de Arquitectura de Tickets (Event-Driven)
**Fase:** Estabilización de Eventos y Timezones en el Monolito.

### 1. Resolución de Ruteo en el Monolito
El Monolito no estaba tomando los cambios del router de eventos.
Se aplicó un `docker restart interno-monolith` forzoso, confirmando la lectura del nuevo código.
El endpoint `/api/v1/events` ahora retorna `202 Accepted` desde el Worker de Tickets.

### 2. Estandarización Multi-Tenant de Timezones (Aware vs Naive)
El framework subyacente requiere PostgreSQL `TIMESTAMP WITH TIME ZONE`. 
Se detectaron columnas desfasadas usando `DateTime` normal. Se auditaron y corrigieron a `DateTime(timezone=True)`:
- `tickets_service`: `OutboxEvent.processed_at`
- `inventory_service`: `Movement.expiry_date`, `CustomsPedimento.customs_date`
- `notification_service`: `CompanyNotificationConfig.created_at/updated_at`, `ProcessedEvent.processed_at`
Se alteraron las columnas en vivo a `TIMESTAMP WITH TIME ZONE USING [column] AT TIME ZONE 'UTC'`.

### 3. Sistema de Prevención de Tormentas de Eventos (Debouncing)
Para prevenir tormentas de escritura de tickets repetidos / spam en el Outbox, se implementó en `TicketRepository.add_outbox_event` un sistema de mitigación:
- **Ventana:** 10 segundos.
- **Validación:** Select + Order By Limit 1 del payload idéntico.
- **Pruebas:** Cobertura exitosa en `test_debouncing.py` (Mockeado con Pytest Asyncio).

### Próximos Pasos (Frontend)
El backend es sólido. Procedemos a habilitar el UI reactivo con Angular Signals, requiriendo llamadas dinámicas de configuración (`/config/constants`) para poblar los selectores contextualmente (`MAINTENANCE` activa `station_id`, `SUPPORT` activa AI, etc).
