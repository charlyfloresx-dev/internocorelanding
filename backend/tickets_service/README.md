# 🎫 Tickets Service — Interno Core

> **Motor Operacional** de la arquitectura Interno Core. Orquesta dinámicamente el piso de producción (MES), el control de inventarios (ERP) y la gestión de usuarios a través de tickets operativos.

## Descripción

El Tickets Service evolucionó de un módulo de soporte (helpdesk) convencional a un **orquestador empresarial** que vincula:

- **Usuarios** → Creación y seguimiento de tickets con historial completo.
- **Producción (MES)** → Paros de línea (`StopLog`) y métricas OEE.
- **Inventarios (ERP)** → Recursos consumidos (`TicketResource`) y rupturas de stock.
- **Notificaciones** → Despacho asíncrono vía Outbox Pattern.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    TICKETS SERVICE                           │
│                                                              │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────┐ │
│  │ ticket_routes │───▷│  TicketService    │───▷│  Models    │ │
│  │   (REST API)  │    │  (Business Logic) │    │  (6 ORM)  │ │
│  └──────────────┘    └──────────────────┘    └────────────┘ │
│         │                     │                              │
│         ▼                     ▼                              │
│  ┌──────────────────┐  ┌───────────────┐                    │
│  │ CommandHandler   │  │  OutboxEvent   │                    │
│  │ (CQRS Pattern)   │  │  (Async Push)  │                    │
│  └──────────────────┘  └───────┬───────┘                    │
│                                  │                            │
└──────────────────────────────────┼────────────────────────────┘
                                   ▼
                          ┌─────────────────┐
                          │  OutboxWorker    │
                          │  (HTTP Dispatch) │
                          └────────┬────────┘
                                   ▼
                        notification_service
```

## Patrones de Diseño

| Patrón | Implementación | Archivo |
|---|---|---|
| **CQRS** | `CreateTicketCommand`, `ConsumeResourcesCommand` | `app/services/ticket_commands.py` |
| **Outbox Pattern** | `OutboxEvent` + `OutboxWorker` (At-Least-Once delivery) | `app/models/outbox.py`, `scripts/outbox_worker.py` |
| **SHA256 Debouncing** | Anti-fatiga para prevenir duplicados en tormentas de eventos | `app/services/ticket_service.py` |
| **Multi-Tenant** | Todos los modelos heredan `MultiTenantBase` (`company_id` filtering) | `app/models/*.py` |
| **Auditoría Forense** | `AuditService.log_action` en `TicketCommandHandler` | `app/services/ticket_commands.py` |

## Modelos de Datos

| Modelo | Tabla | Propósito |
|---|---|---|
| `Ticket` | `tickets` | Entidad principal con métricas MES/ERP |
| `TicketComment` | `ticket_comments` | Comentarios de usuarios por ticket |
| `TicketHistory` | `ticket_history` | Historial de cambios (status, prioridad, asignación) |
| `TicketResource` | `ticket_resources` | Materiales consumidos (weak FK → `inventory_service`) |
| `StopLog` | `ticket_stop_logs` | Paros de producción (weak FK → `mes_service`) |
| `OutboxEvent` | `outbox_events` | Cola transaccional de eventos de integración |

## API Endpoints

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| `POST` | `/api/v1/tickets/` | Crear ticket | JWT Bearer |
| `GET` | `/api/v1/tickets/` | Listar tickets (multi-tenant) | JWT Bearer |
| `GET` | `/api/v1/tickets/{id}` | Detalle de ticket | JWT Bearer |
| `PATCH` | `/api/v1/tickets/{id}` | Actualizar ticket | JWT Bearer |
| `POST` | `/api/v1/tickets/{id}/comments` | Agregar comentario | JWT Bearer |
| `GET` | `/health` | Health check | Público |

### Formato de Respuesta

Todas las respuestas siguen el contrato estándar del frontend:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Operación exitosa",
  "meta": {}
}
```

## Lógica Industrial

### Debouncing SHA256

Cuando el `inventory_service` emite eventos de ruptura de stock o niveles bajos, el sistema genera un hash:

```
SHA256(company_id + warehouse_id + product_id + priority) → deduplication_hash
```

Si ya existe un ticket **ABIERTO** (`NEW` | `IN_PROGRESS`) con el mismo hash, se retorna el existente sin crear duplicado. Esto previene la "tormenta de tickets" durante ráfagas de eventos del sensor de inventario.

### Métricas Operativas

Cada ticket puede rastrear:
- `module_origin` — Módulo de origen (PRODUCTION, INVENTORY)
- `area` — Área de la planta
- `estimated_time` / `real_time_spent` — En minutos
- `cost_estimate` — Costo estimado de resolución

### Reference Codes

Formato: `TKT-{AÑO}-{SECUENCIA}` (ej: `TKT-2026-0001`)

## Eventos de Integración

### TicketCreatedEvent (Outbox)

```json
{
  "event_id": "uuid",
  "event_type": "TicketCreatedEvent",
  "timestamp": "2026-03-08T12:00:00Z",
  "version": "1.0",
  "ticket_id": "uuid",
  "company_id": "uuid",
  "reference_code": "TKT-2026-0001",
  "title": "Ruptura de stock en Almacén Norte",
  "ticket_type": "Incidencia",
  "priority": "Alta",
  "created_by_id": "uuid",
  "metadata": {}
}
```

El `OutboxWorker` procesa estos eventos y los despacha al `notification_service` vía HTTP POST.

## Infraestructura

| Componente | Valor |
|---|---|
| **Runtime** | Python 3.11 |
| **Framework** | FastAPI 0.104.1 |
| **ORM** | SQLAlchemy 2.0.23 (async) |
| **Database** | PostgreSQL (asyncpg) |
| **Container** | Docker (non-root user) |
| **Port** | 8000 |

### Docker Build

```bash
# Contexto de build: /backend (raíz)
docker build -f tickets_service/Dockerfile -t interno-backend-tickets-service .
```

### Variables de Entorno

Configuradas vía `common.config.InternoSettings`:

| Variable | Default |
|---|---|
| `INT_DATABASE_URL` | `postgresql+asyncpg://user:password@localhost/dbname` |
| `INT_SECRET_KEY` | `local-dev-secret-key-InternoCore` |
| `INT_ALGORITHM` | `HS256` |

## Dependencias

- `common` — Modelos base, audit, middleware, seguridad
- `auth-service` — Validación local de JWT

## Backlog Pendiente

- [ ] Integración de `ConsumeResourcesCommand` con Kardex del `inventory_service`
- [ ] Tests automatizados (debouncing, HMAC, outbox)
- [ ] Endpoints GraphQL/REST para KPIs industriales (MTTR, MTBF, OEE)
- [ ] Verificación de firma HMAC para endpoints inter-servicio
- [ ] Background Consumer para actualizaciones de estado originadas en otros servicios
