# Consolidated Tasks — 2026-05-01

## Jornada: Tickets Service — Motor Operacional Industrial

### Contexto
El Tickets Service fue auditado y remediado para cumplir con los estándares de Interno Core (Fase 2-3 del proyecto). Posteriormente se expandió su modelo de dominio para soportar 4 flujos operacionales industriales.

---

## ✅ Tareas Completadas

### 1. Remediación Crítica (Fase 4)
- [x] Migrar `cost_estimate` de `float` a `Numeric(18, 8)` en `ticket.py`
- [x] Actualizar `TicketRead` DTO para usar `Decimal` en `cost_estimate`
- [x] Migrar `quantity` de `float` a `Decimal` en `ConsumeResourceDto`
- [x] Implementar HMAC-SHA256 en endpoint `/internal` con `SECRET_KEY`
- [x] Agregar `AuditService.track()` para intentos de acceso no autorizados (firma ausente/inválida)
- [x] Reemplazar `audit_repo.create_log` por `AuditService.track()` en `TicketCommandHandler`
- [x] Alinear `SECRET_KEY` en `docker-compose.yml` (`changeme` → `DEV_SECRET_KEY_CAMBIAME_EN_PROD_12345`)
- [x] Extender vigencia de suscripciones seed a 10 años (`timedelta(days=3650)`)

### 2. Validación en Docker (Pruebas Live)
- [x] Levantar `tickets-service`, `auth-service`, `subscription-service` en Docker
- [x] Ejecutar seed de suscripciones para las 4 empresas
- [x] Test 1 (HMAC): POST `/internal` con firma inválida → `403 Forbidden` ✅
- [x] Test 2 (Precisión): Verificar `Decimal("0.00000001")` en DTO ✅
- [x] Test 3 (Auditoría): Logs forenses con `AuditService.track` ✅

### 3. Expansión del Modelo de Dominio (Fase 5)
- [x] Expandir `TicketType` enum: +4 valores (`Mantenimiento`, `Recibo Material`, `Tiempo Muerto`, `Escalación`)
- [x] Expandir modelo `Ticket`: +7 campos operacionales
  - `source_service`, `station_id`, `reported_by_id`, `parent_ticket_id`
  - `auto_close_on_event`, `escalation_level`, `resolved_at`
- [x] Expandir DTOs: `TicketRead`, `TicketCreate`, `TicketUpdate`, `InternalTicketCreate`
- [x] Expandir `CreateTicketCommand` con campos operacionales
- [x] Expandir handler para propagar campos al repositorio
- [x] Self-referential relationship: `parent_ticket` ↔ `child_tickets`
- [x] Docker rebuild + Uvicorn startup exitoso

### 4. Documentación
- [x] Actualizar `SERVICE_LOG.md` con Fase 4 y Fase 5
- [x] Actualizar `REPO_LOG.md` con Phase 75
- [x] Crear plan de implementación (`tickets_operational_expansion_plan.md`)

---

## 📋 Backlog Pendiente (Próximas Sesiones)

### Fase 6: Notificaciones y Estado Reactivo
- [ ] Crear `NotificationDispatcher` con integración Outbox
- [ ] Implementar `TicketStatusChangedEvent`
- [ ] Endpoint `/internal/confirm-kardex-entry` para auto-cierre de recibos
- [ ] Integrar dispatcher en `TicketService.update_ticket`

### Fase 7: Motor de Escalación Dinámica
- [ ] Definir `ESCALATION_MATRIX` por área/puesto
- [ ] Crear `EscalationWatcher` background worker
- [ ] Implementar firma forense (`operator_hash`) en escalaciones
- [ ] `TicketEscalatedEvent` para notificaciones

### Fase 8: Mantenimiento + StopLog Automático
- [ ] Auto-generar `StopLog` en tickets `MAINTENANCE` + `Crítica`
- [ ] Calcular costo de oportunidad por downtime
- [ ] Actualizar `downtime_minutes` al resolver

### Fase 9: Dashboard Industrial (KPIs)
- [ ] Endpoints REST: MTTR, MTBF, OEE impact
- [ ] Tasa de escalación y cumplimiento SLA

### Infraestructura Pendiente
- [ ] Generar migración Alembic para Fase 5
- [ ] Resolver el `companyId` vs `company_id` mismatch en `TokenPayload` para el test E2E
- [ ] Tests automatizados para debouncing y escalación
