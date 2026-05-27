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

### P4: Timezone por empresa

> **Contexto:** Todos los microservicios almacenan fechas en UTC. La UI muestra en timezone del browser.
> Se necesita que cada empresa tenga su propia timezone (`America/Monterrey`, `America/Chicago`, etc.)
> y que la UI y los reportes muestren fechas en la timezone de la empresa activa.

**Diseño:**
- `company_settings` (o `hr_tenant_configs`) agrega columna `timezone: str` (IANA: `America/Monterrey`)
- Default: `UTC`
- JWT claim: añadir `timezone` al payload al hacer select-company
- Frontend: `AuthService` expone `companyTimezone()` signal; pipes de fecha usan ese timezone
- Backend: ningún cambio de almacenamiento (siempre UTC en DB); solo serialización en respuesta

**Tareas:**
- `[ ]` `master_data_service` o `auth_service`: columna `timezone` en tabla de configuración de empresa
- `[ ]` Migration + seed defaults (`America/Monterrey` para empresas MX, `America/Chicago` para US)
- `[ ]` `auth_service`: incluir `timezone` en JWT claims al hacer `select-company`
- `[ ]` `common/schemas/jwt_claims.py`: campo `timezone: str = "UTC"` en el modelo de claims
- `[ ]` Frontend `AuthService`: exponer `companyTimezone = computed(() => session().timezone ?? 'UTC')`
- `[ ]` Frontend: pipe `LocalDatePipe` usando `date-fns-tz` o `Intl.DateTimeFormat` con el timezone de empresa
- `[ ]` Inputs `datetime-local`: al leer el valor del input (que es local browser), convertir a UTC antes de enviar; al mostrar, convertir UTC → company timezone

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

---

## Phase 144 Tasks Completadas (sesión tarde 2026-05-27)

### tickets_service — visibilidad `/mine`
- [x] `list_by_visibility`: filtra solo ASIGNADOS (no created_by)
- [x] Cubre Triple Identity: INTERNAL via `assigned_to_id` + `ticket_assignees INTERNAL`
- [x] Parámetros opcionales `collaborator_id` + `external_contact_id` para PLANTA/EXTERNO
- [x] `ticket_assignees` coverage con EXISTS subqueries (tickets triageados sin `assigned_to_id`)
- [x] Rebuild tickets-service OK

### scanner (uber_pos_layout.md)
- [x] Tarjeta carrito: solo código de producto (sin nombre)
- [x] Scan duplicado: snackbar una vez → silencio (`_warnedDuplicates`)
- [x] `scanWindow` restringido al cutout visual

### CAPA mobile
- [x] Checkbox circular (44px) reemplaza botón "Cerrar"
- [x] AnimatedContainer: vacío → verde con check al cerrar

### audit_logs
- [x] Verificado `audit_logs` en `hcm_db` ✅ EXISTS
- [x] Verificado `audit_logs` en `subscription_db` ✅ EXISTS

### Pendiente futuro
- [ ] Pasar `collaborator_id` desde el perfil del móvil al endpoint `/mine`
- [ ] Limpiar `_warnedDuplicates` en `RemoveItem` individual (low priority)

---

## PENDIENTES — HCM Service: Gaps Legacy Employee → Collaborator

> **Contexto (sesión 2026-05-27):** Análisis del legacy .NET `Employee.cs` vs. Python `Collaborator`.
> El colaborador en HCM es el equivalente directo al `Employee` del legacy.
> `Department` del HCM ES la configuración de áreas por empresa — el dropdown de Área
> en la pantalla Soporte del móvil ya lo consume vía `GET /api/v1/hcm/departments/`.
> El legacy también distingue `Area` (física/planta) de `Department` (funcional);
> en el HCM actual ambos están fusionados en `Department`.

### P-HCM-1: `Department.description` + seed por defecto ✅ COMPLETADO (sesión 2026-05-27)

- [x] Campo `description: Optional[str]` añadido al modelo `Department`
- [x] Migración `003_add_department_description.py` (alembic hcm_service)
- [x] Seed de departamentos por defecto en `hcm_service/scripts/seed.py`:
  Producción · Calidad · Mantenimiento · Almacén · Administración · Ingeniería

### P-HCM-2: CRUD de Departamentos en Angular (configuración por empresa) 🟡

> Los departamentos son configurados por empresa desde el portal web.
> El endpoint ya existe (`GET/POST/PATCH/DELETE /hcm/departments/`); falta la UI.

- `[ ]` Sección "ÁREAS Y DEPARTAMENTOS" en la pantalla de configuración de empresa
- `[ ]` Lista de departamentos con toggle `is_active`
- `[ ]` Formulario de creación: Nombre + Código + Descripción
- `[ ]` Confirmación antes de desactivar (afecta dropdown en móvil)

### P-HCM-3: Gaps de campos del legacy (deuda baja prioridad) 🟢

> Ninguno bloquea funcionalidad actual. Se puede hacer en una fase futura.

- `[ ]` `JobPosition` como catálogo propio (actualmente solo `job_title: str` en Collaborator)
- `[ ]` `shift_id` en Collaborator → FK al turno del MES (bridge HCM↔MES)
- `[ ]` `manager_id` + `director_id` (jerarquía 3 niveles, actualmente solo `supervisor_id`)
- `[ ]` `is_hourly: bool` (directo horario vs. salarial)
- `[ ]` `departure_date: Optional[date]` (baja voluntaria / baja definitiva)
- `[ ]` `business_unit_id` → catálogo `BusinessUnit` (usado en empresas multi-planta tipo Safran)
- `[ ]` `Department.description` en Angular CRUD (campo ya en DB desde P-HCM-1)

---

## PENDIENTES — MES Service: Flujo ERP → MES → Production Report

> **Contexto:** El MES ejecuta el ciclo completo: ERP libera Work Orders → MES las recibe, asigna recursos,
> registra operadores y tiempos de ciclo → al cerrar corrida, reporta producción de vuelta al ERP.
> El análisis de 2026-05-27 identificó gaps que bloquean el flujo end-to-end.

---

### P-MES-1: Bugs Críticos (bloquean creación de Work Orders) 🔴

**Problema:** `WorkOrderHandler.handle_create` intenta setear campos que NO existen en el modelo `WorkOrder`.
La creación falla silenciosamente con `AttributeError`.

| Handler usa | Modelo tiene | Acción |
|---|---|---|
| `order_qty=` | `order_quantity` | Renombrar campo en modelo O handler |
| `due_date=` | `request_date` | Renombrar / alinear |
| `alias=` | *(no existe)* | Agregar columna `alias: Optional[str]` |
| `release_date=` | *(no existe)* | Agregar columna `release_date: Optional[datetime]` |
| `status="PLANNED"` | default `"DRAFT"` | Alinear — PLANNED es el estado correcto al recibir del ERP |

**Archivos:** `mes_service/mes_app/models/work_order.py` + `mes_service/mes_app/core/handlers/work_order_handler.py`

- `[ ]` Sincronizar modelo `WorkOrder` con los campos que usa el handler
- `[ ]` Agregar migración Alembic para las columnas nuevas (`alias`, `release_date`)
- `[ ]` Verificar que `GET /work-orders/` y `GET /work-orders/{order_number}` no rompen con campos añadidos

---

### P-MES-2: Bug BOM — `parent_item_code` inexistente 🔴

**Archivo:** `inventory_service/inventory_app/models/bom.py:24`

El `__repr__` referencia `self.parent_item_code` pero el campo no está mapeado en la clase.
El modelo tiene `product_id` (UUID del producto padre) pero no una columna `parent_item_code` (string legible).

- `[ ]` Opción A: Agregar `parent_item_code: Mapped[str]` al modelo `BOM` + migración
- `[ ]` Opción B: Corregir `__repr__` para usar `product_id` en lugar de `parent_item_code`
- `[ ]` Verificar si `seed_variants.py` o seeds industriales usan `parent_item_code` → puede requerir opción A

---

### P-MES-3: Backflush de materiales al cerrar corrida 🟠

**Contexto:** Cuando `CloseProductionRunCommand` cierra una corrida, los componentes del BOM
deben consumirse del inventario (movimiento OUT por backflush). Actualmente hay un comentario
`# Here we would normally emit a Domain Event` — no hay implementación.

**Restricción arquitectónica:** MES NO puede importar modelos de `inventory_service`.
La integración DEBE ser via HTTP (`httpx`) al endpoint `POST /api/v1/inventory/movements`.

**Archivo:** `mes_service/mes_app/core/commands/close_production_run.py:77`

- `[ ]` Crear `mes_service/mes_app/infrastructure/clients/inventory_client.py`
  — `InventoryClient.backflush(company_id, bom_components: list[dict], reference_run_id)` via `httpx`
- `[ ]` En `CloseProductionRunCommand.execute()`: resolver componentes del BOM por `item_code` y llamar backflush
- `[ ]` Manejar fallo del cliente HTTP como warning (no revertir el cierre de corrida si inventario falla)
- `[ ]` Agregar `material_status` en `WorkOrder` para reflejar si el backflush fue exitoso o quedó pendiente

---

### P-MES-4: Actualizar progreso de Work Order al reportar producción 🟠

**Problema:** Cuando se registra producción (`ManufacturingLedger` / `ProductionEvent`),
el campo `manufactured_quantity` de `WorkOrder` nunca se actualiza.
La WO no sabe cuánto se ha producido acumulado.

- `[ ]` En `ProductionService.register_event()` o en `CloseProductionRunCommand`:
  al cerrar corrida, sumar `actual_quantity` al `WorkOrder.manufactured_quantity`
- `[ ]` Transición automática de status:
  - `RELEASED` → `IN_PROGRESS` al registrar primera pieza
  - `IN_PROGRESS` → `COMPLETED` cuando `manufactured_quantity >= order_quantity`
- `[ ]` Endpoint `GET /work-orders/{order_number}` debe incluir `manufactured_quantity` + `completion_pct`

---

### P-MES-5: Soporte Tab — Crear Ticket en móvil 🟡

> **Contexto (sesión 2026-05-27):** El usuario mostró screenshots de la tab "Soporte" del móvil
> (actualmente muestra "BANDEJA DE ENTRADA") y el formulario Angular de CREAR TICKET.
> La instrucción fue: *"La pantalla de soporte es para generar un ticket tal cual en el frontend,
> dejalo como tareas pendientes"*

**Angular CREAR TICKET tiene los campos:** Asunto · Prioridad · Área · Descripción

El móvil ya tiene `create_ticket_screen.dart` implementado (Asunto, Prioridad, Descripción).
La tab de Soporte (`InboxScreen`) es actualmente una pantalla de notificaciones estática.

- `[ ]` Revisar si reemplazar `InboxScreen` por `CreateTicketScreen` en la tab Soporte o hacer split (tab con dos vistas)
- `[ ]` Agregar campo **Área** al formulario móvil (falta vs. Angular)
- `[ ]` Conectar `CreateTicket` event del `TicketsBloc` al endpoint `POST /tickets/`
- `[ ]` Mostrar confirmación de éxito y navegar a la lista de tickets después de crear
# Task: Multitenant Timezone Support

## Backend
- [x] 1. Modify `common/models/company.py` — add `timezone` column
- [x] 2. Create Alembic migration in `auth_service`
- [x] 3. Create Alembic migration in `master_data_service`
- [x] 4. Modify `security.py` — add timezone to JWT payload
- [x] 5. Modify `select_company_command.py` — load & inject timezone
- [x] 6. Modify `schemas/auth.py` — add timezone to AccessTokenResponse
- [x] 7. Modify `auth.py` endpoints — populate timezone in /refresh and /me
- [x] 8. Modify `unified_industrial_seed.py` — seed timezone defaults

## Frontend
- [x] 9. Modify `domain.types.ts` — add timezone to AuthSession
- [x] 10. Modify `auth.service.ts` — expose companyTimezone computed signal
- [x] 11. Create `local-date.pipe.ts` — standalone LocalDatePipe
- [x] 12. Swap `| date` → `| localDate` in key components
