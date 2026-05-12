# 🏗️ Estado General del Backend — InternoCore
**Fecha**: 2026-03-04 | **Referencia técnica**: Fases 1‑10

---

## 📊 Completitud por Microservicio

| # | Microservicio | Puerto | % | Estado |
|---|---------------|--------|---|--------|
| 1 | `auth_service` | 8000 | **95%** | ✅ Production-ready |
| 2 | `common` | — | **92%** | ✅ MultiTenantBase, auth, middleware completos |
| 3 | `master_data_service` | 8003 | **88%** | ✅ Estable |
| 4 | `subscription_service` | 8005 | **85%** | ✅ Estable |
| 5 | `inventory_service` | 8006 | **82%** | ✅ Ledger inmutable operativo |
| 6 | `wms_service` | 8007 | **78%** | ✅ Reservas y tránsitos integrados |
| 7 | `tickets_service` | 8004 | **75%** | 🟡 Motor operativo listo |
| 8 | `notification_service` | 8008 | **65%** | 🟡 Event consumer + PreferenceService |
| 9 | `mes_service` | 8002 | **40%** | 🔴 Solo scaffolding |

**Completitud global estimada: ~76% (Production-Grade Beta)**

---

## 🔍 ¿Qué le falta a cada servicio para llegar al 100%?

### ✅ `auth_service` — 95% | Falta 5%
- [ ] Tests unitarios: login T1/T2, `select-company`, roles edge cases
- [ ] Refresh token: renovación de JWT sin re-login
- [ ] Rate limiting en `/login` (anti brute-force)

### ✅ `common` — 92% | Falta 8%
- [ ] Tests de middleware (propagación de [company_id](file:///c:/API/interno/backend/common/domain/entities.py#63-66))
- [ ] Exportar [BaseProvider](file:///c:/API/interno/backend/notification_service/app/services/providers.py#22-32) aquí para uso cross-service

### ✅ `master_data_service` — 88% | Falta 12%
- [ ] Endpoint bulk-import de UOM
- [ ] Tests de `conversion_factor` con decimales extremos
- [ ] Paginación avanzada con filtros compuestos en `/products`

### ✅ `subscription_service` — 85% | Falta 15%
- [ ] Worker de renovación automática de suscripciones
- [ ] Alertas P2 cuando quedan < 7 días de vigencia
- [ ] Tests de módulo-gating (rechazar requests de módulos bloqueados)

### ✅ `inventory_service` — 82% | Falta 18%
- [ ] Tests automatizados: overselling, reconciliación, reservas
- [ ] [transit_worker.py](file:///c:/API/interno/backend/inventory_service/scripts/transit_worker.py) — definido, pendiente de implementar
- [ ] `reorder_point` y `critical_stock` dinámicos por producto/empresa
- [ ] Confirmar Alembic migrations en Docker sin conflictos

### 🟡 `wms_service` — 78% | Falta 22%
- [ ] Fulfillment parcial (despacho parcial cuando stock es insuficiente)
- [ ] Tests: confirmar que [ConfirmDocumentHandler](file:///c:/API/interno/backend/wms_service/app/application/handlers.py#107-259) propaga `transaction_id`
- [ ] Cancelación de orden → `release_stock` automático
- [ ] Flujo de devoluciones (`TRANSFER_RETURN`)

### 🟡 `tickets_service` — 75% | Falta 25%
- [ ] [ConsumeResourcesCommand](file:///c:/API/interno/backend/tickets_service/app/services/ticket_commands.py#28-33) → integración real con `inventory_service` (Kardex OUT)
- [ ] Endpoints de métricas: MTTR, MTBF, OEE para frontend
- [ ] State machine formal: OPEN → IN_PROGRESS → RESOLVED → CLOSED
- [ ] SLA escalation automática (P1 sin resolver en 4h → notificar OWNER)
- [ ] Correr tests de debouncing en CI

### 🟡 `notification_service` — 65% | Falta 35%
- [ ] Providers reales: [EmailProvider](file:///c:/API/interno/backend/notification_service/app/services/providers.py#34-41) (SendGrid/SMTP), [PushProvider](file:///c:/API/interno/backend/notification_service/app/services/providers.py#43-50) (FCM)
- [ ] Tests E2E: Outbox → Worker → Consumer → Notification
- [ ] `NotificationTemplates` model + endpoints (definido en plan, no implementado)
- [ ] Retry / dead-letter con backoff cuando provider externo falla
- [ ] Soporte de nuevos event types: `StockBreakAlert`, `LineStoppedEvent`, `SubscriptionExpiring`

### 🔴 `mes_service` — 40% | Falta 60%
- [ ] Lógica de Work Orders: creación, asignación y cierre
- [ ] OEE Calculator (Disponibilidad × Rendimiento × Calidad)
- [ ] Integración [StopLog](file:///c:/API/interno/backend/tickets_service/app/models/stop_log.py#6-23) desde `tickets_service` para calcular downtime
- [ ] Producción por lotes (`lot_number`, `batch_id`, trazabilidad)
- [ ] Ningún endpoint real operativo (solo scaffolding)

---

## 🧩 Cobertura Funcional del Ecosistema

| Capacidad | Cobertura |
|-----------|-----------|
| Autenticación Multi-tenant (T1/T2) | ✅ 100% |
| Autorización RBAC por empresa | ✅ 100% |
| Consola de Auditoría + Force-Release | ✅ 100% |
| Ledger de Inventario (Kardex inmutable) | ✅ 95% |
| Reservas atómicas + lógica In-Transit | ✅ 90% |
| Outbox Pattern (mensajería confiable) | ✅ 90% |
| Gestión de Productos y UOM | ✅ 90% |
| Alertas automáticas P1‑P4 (Debouncing) | ✅ 85% |
| Control de Suscripciones y módulos | ✅ 85% |
| Motor de Tickets MES/ERP (CQRS) | 🟡 80% |
| Dispatch de notificaciones por canal | 🟡 65% (providers simulados) |
| Tests automatizados | 🔴 30% (estructurados, sin CI) |
| Infraestructura AWS (ECR/S3/CF/CI-CD) | 🔴 0% (planeado) |

---

## 🚦 Bloqueos Principales para llegar al 100%

| Prioridad | Bloqueo | Impacto |
|-----------|---------|---------|
| 🔴 Crítico | Tests automatizados (unitarios + E2E) | Bloquea CI/CD y deploy seguro |
| 🔴 Crítico | `mes_service` sin lógica | Bloquea OEE y producción |
| 🟡 Alto | Providers reales en `notification_service` | Sin Email/Push real el sistema es sordo |
| 🟡 Alto | Fulfillment parcial en `wms_service` | Sin esto no hay operaciones reales |
| 🔴 Crítico | Infraestructura AWS | Sin ECR/S3/CF no hay deploy en producción |
