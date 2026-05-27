# Consolidado de Tareas: 2026-05-27

Jornada de tickets: corrección de loop infinito en Angular, fix de triage multi-asignados, implementación de TicketActions (CAPA), y plan arquitectónico para sistema de KPIs cross-service y tabla de multi-asignados.

---

## Phase 142 — Tickets CAPA + Triage Fix + KPI Plan ✅ COMPLETADO

### Bugs Resueltos

- `[x]` **Loop infinito en Angular** — `selectedIdentities()` leído sin `untracked()` dentro del efecto del SideDrawer al llamar `_syncIds()`. Fix: `untracked(() => this.selectedIdentities())` en `tickets-form.component.ts`
- `[x]` **`ngOnInit` fetcheaba toda la lista al abrir un ticket** — `loadTickets()` corría siempre aunque ya estuviera en modo triage. Fix: guard `if (this.view() !== 'triage')` en `ngOnInit()`
- `[x]` **Triage solo guardaba `assigned_to_id`** — `TicketTriage` schema no tenía `collaborator_id` ni `external_contact_id`. Pydantic los ignoraba. `ticket_service.py` usaba `getattr(cmd, "new_collaborator_id", None)` → siempre `None`. Fix: campos añadidos al schema, service los lee directamente
- `[x]` **Kanban mostraba solo un asignado** — columna EN PROCESO solo mostraba `assigned_to_id`. Fix: método `getAssignedLabels()` con chips para INTERNAL/PLANTA/EXTERNO

### TicketActions (CAPA) implementado

- `[x]` Modelo `TicketAction` — descripción, Triple Identity, commit_date, escalation_date, closed_date, is_closed
- `[x]` Migración `003_add_ticket_actions.py` — tabla `ticket_actions` con 4 índices
- `[x]` Endpoint `POST /tickets/{id}/actions` (scope: `ticket:triage`)
- `[x]` Endpoint `GET /tickets/{id}/actions` (scope: `ticket:read`)
- `[x]` Endpoint `PATCH /tickets/{id}/actions/{aid}/close` (scope: `ticket:triage`)
- `[x]` Schemas Pydantic: `TicketActionCreate` + `TicketActionClose` + `TicketActionRead`
- `[x]` `TicketRead` ahora incluye `actions: []`
- `[x]` Frontend: tipo `TicketAction` + 3 métodos en `SupportService`
- `[x]` Frontend: sección "PLAN DE ACCIONES" en drawer de triage (lista + formulario + cierre)

### Flujo confirmado

- `[x]` Downtime (MES) → Ticket (type=DOWNTIME) → TicketActions (CAPA correctivos) → KPIs impactados

---

## PENDIENTES — Phase 143+

### P1: Multi-asignados (tabla `ticket_assignees`)

> **Contexto:** Actualmente los tickets tienen 3 columnas `assigned_to_id / collaborator_id / external_contact_id` (un valor por tipo). Se necesita soportar múltiples usuarios, colaboradores y proveedores por ticket.

**Diseño tabla:**
```
ticket_assignees
  id, ticket_id, company_id, tenant_id
  identity_type: ENUM(INTERNAL, PLANTA, EXTERNO)
  identity_id: UUID (weak ref — sin FK cross-service)
  is_lead: bool  ← responsable principal
  assigned_at: datetime
  assigned_by: UUID
```

**Tareas:**
- `[ ]` Migration `004_add_ticket_assignees.py` + backfill desde columnas legacy
- `[ ]` Nuevos endpoints: `POST /tickets/{id}/assignees` + `DELETE /tickets/{id}/assignees/{id}`
- `[ ]` Actualizar triage para escribir en tabla (mantener columnas legacy por compat)
- `[ ]` `TicketRead` devuelve `assignees: []` además de 3 campos legacy
- `[ ]` Frontend: chips multi-asignados desde tabla (no solo 3 campos)
- `[ ]` Deprecar columnas `assigned_to_id / collaborator_id / external_contact_id` en Phase posterior

---

### P2: Sistema de KPIs Cross-Service (`kpi_service`)

> **Contexto:** KPIs se generan en MES (OEE, MTTR), Inventory (stock accuracy, turnover), WMS (pick accuracy), Tickets (SLA, backlog). Se necesita un sistema unificado. Los KPIs también se vinculan a `TicketActions` (cada acción impacta métricas).
>
> **Decisión arquitectónica:** Nuevo `kpi_service` (puerto 8010, `kpi_db`). No va en `mes_service` (scope demasiado estrecho) ni en `common/` (contamina infraestructura compartida con dominio). Los servicios empujan lecturas via endpoint interno HMAC.

**Modelos (en `kpi_service`):**

```python
KPIDefinition     # Catálogo: code, name, category, unit, frequency,
                  # calculation_method, data_source, higher_is_better
                  # → ScoreCard.KPI + Category + CalculationMethod + DataSource + Frecuency

KPITarget         # Meta por período con Soft-Close pattern
                  # kpi_id, period_label, target_value, weight, valid_from, valid_until
                  # → ScoreCard.Target + FullScore

KPIReading        # Time series de lecturas reales
                  # kpi_id, period_label, reading_date, actual_value, source, recorded_by
                  # → ScoreCard.Performance
```

**Modelo en `tickets_service`:**
```python
ActionKPILink     # Weak ref por kpi_code (string, no FK cross-service)
                  # action_id, kpi_code, expected_delta, impact_direction
```

**En `common/` (solo tipos, sin ORM):**
```python
# common/models/kpi_types.py
class KPICategory(str, Enum): Quality | Delivery | Cost | Safety | Maintenance | Supplier
class KPIFrequency(str, Enum): Daily | Weekly | Monthly | Quarterly
```

**Tareas:**
- `[ ]` Crear `kpi_service` — Dockerfile, entrypoint, alembic, config base
- `[ ]` Modelos `KPIDefinition + KPITarget + KPIReading` + migración
- `[ ]` Endpoint interno HMAC `POST /internal/kpi/readings` (recibe lecturas de cualquier servicio)
- `[ ]` `common/models/kpi_types.py` — enums compartidos (KPICategory, KPIFrequency)
- `[ ]` `ActionKPILink` table en `tickets_service` — migración `004_add_action_kpi_link.py`
- `[ ]` Seed de KPIs industriales estándar: OEE, MTTR, FPY, OTD, SCRAP_RATE, STOCK_ACCURACY, PICK_ACCURACY, SLA_COMPLIANCE
- `[ ]` Push lecturas desde `mes_service` al cerrar Downtime (MTTR, availability)
- `[ ]` Push lecturas desde `tickets_service` al cerrar ticket DOWNTIME (resolution time, SLA)
- `[ ]` UI: selector de KPIs impactados al crear `TicketAction` (search por code + name)
- `[ ]` Dashboard de métricas vs targets por período

---

### P3: Deuda técnica tickets — pendiente desde sesiones anteriores

- `[ ]` Fix: `kiosk_service` CORS `allow_origins=["*"]` — CRÍTICO (Phase 133 identificado, no corregido)
- `[ ]` Fix: `asset_manager_service` CORS fallback a `["*"]` — ALTO
- `[ ]` Fix: God Mode `==` → `hmac.compare_digest` en `common/security/dependencies.py`
- `[ ]` Fix: `https://*.vercel.app` wildcard en `common/config.py`
- `[ ]` Fix: colaboradores de otras empresas del grupo no aparecen en search de triage (usar `group_id` vs `company_id`)
- `[ ]` Deploy: reconstruir `tickets-service` para aplicar migración `003_add_ticket_actions`:
  ```powershell
  docker compose -f infrastructure/docker/docker-compose.dev.yml up -d --build tickets-service
  ```

---

## Contexto técnico para próxima sesión

### Angular Signals — SideDrawer Effect (no olvidar)
El efecto del `SideDrawerComponent` trackea `drawerService.component()` y `drawerService.data()`. Cualquier signal leído **síncronamente** dentro de `set data(val)` se convierte en dependencia reactiva del efecto. Si esa dependencia cambia luego (async), el efecto re-corre y destruye/recrea el componente → loop.

**Regla:** Cualquier signal leído dentro de `set data(val)` o métodos llamados desde él **DEBE** usar `untracked()`.

Signals actualmente protegidos con `untracked()`:
- `this.userMap()` en `_prePopulateAssignment()`
- `this.selectedIdentities()` en `_syncIds()`

### Backend tickets — campos clave
- `ticket_assignees` todavía NO implementada — sigue usando 3 columnas simples
- `ticket_actions` implementada pero contenedor pendiente de rebuild
- `TicketTriage.collaborator_id` + `TicketTriage.external_contact_id` ya en schema (Phase 142)

### KPI Service — decisión tomada
- Puerto propuesto: **8010**
- DB: `kpi_db`
- Patrón de lectura: push via `POST /internal/kpi/readings` con HMAC `X-Service-Signature`
- Refs cross-service: por `kpi_code: str` (no UUID FK) — igual que `collaborator_id` en tickets
