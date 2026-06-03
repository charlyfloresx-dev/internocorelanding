# Phase 172 — Tab "Soporte" en Resource Monitor

**Estado:** En Progreso  
**Inicio:** 2026-06-02  
**Responsable:** Sistema de Monitoreo Industrial  
**Prioridad:** MEDIA  

---

## Resumen Ejecutivo

Reemplazar el botón estático "Andon Activo" con un tab dinámico "Soporte" que muestre en tiempo real:
1. **Tickets activos** del recurso (filtrados por `station_id`)
2. **Equipo de soporte** del área (agrupado por `production_area_id`)
3. **Acciones rápidas** por ticket (Asignar, Resolver, Comentar, Escalar)

Permite al supervisor gestionar incidencias sin navegar fuera del monitor visual de producción.

---

## Plan de Implementación por Fases

### FASE 1: Backend — Filtros de Tickets ✅ COMPLETADO

**Objetivo:** Habilitar `GET /tickets?station_id=X&status=Y`

**Archivos modificados:**
- `backend/tickets_service/tickets_app/infrastructure/repositories/ticket_repository.py`
  - Actualizado `list_by_company()` con parámetros opcionales `station_id`, `status`
  
- `backend/tickets_service/tickets_app/services/ticket_service.py`
  - Actualizado `get_tickets()` para pasar los filtros al repositorio
  
- `backend/tickets_service/tickets_app/routers/ticket_routes.py`
  - Actualizado router `GET /` con query parameters documentados

**Resultado:**
```bash
GET /api/v1/tickets?station_id=<resource.id> → lista de tickets abiertos
```

---

### FASE 2: Frontend — TicketService + Types ✅ COMPLETADO

**Objetivo:** Preparar servicio Angular para cargar tickets por recurso

**Tareas:**
- [x] Extender `TicketService` con método `loadByStation(resourceId: string)`
  - ✅ Usa signals `stationTickets`, `loadingStation`
  - ✅ Filtra solo tickets NO resueltos
  
- [x] Verificar tipos en `domain.types.ts`
  - ✅ Añadido campo `station_id?: string` a interfaz `Ticket`
  
- [x] Importar `TicketService` en `resource-monitor.component.ts`
  - ✅ Inyectado: `readonly ticketSvc = inject(TicketService)`

- [x] Métodos helpers para renderización:
  - ✅ `getPriorityCss(priority)` — mapea prioridad a clase Tailwind
  - ✅ `getPriorityChipCss(priority)` — chip de prioridad
  - ✅ `getStatusCss(status)` — mapea estado a clase Tailwind
  - ✅ `isAssignableStatus(status)` — valida si se puede asignar
  - ✅ `isResolvableStatus(status)` — valida si se puede resolver
  - ✅ Métodos stub para acciones: `openNewTicket()`, `assignTicket()`, `resolveTicket()`, `commentTicket()`, `escalateTicket()`

**Archivos Modificados:**
- `frontend/src/app/core/services/ticket.service.ts` ✅
- `frontend/src/app/core/models/domain.types.ts` ✅ (+ station_id)
- `frontend/src/app/modules/monitor/resource-monitor.component.ts` ✅

**Resultado:**
- ✅ Build exitoso: `Application bundle generation complete`
- ✅ TypeScript compilation: 0 errors
- ✅ TicketService cargable y funcional

---

### FASE 3: Frontend — Estructura del Tab

**Objetivo:** Renderizar el tab "Soporte" vacío (sin datos aún)

**Tareas:**
- [ ] Tipo `MainTab = 'produccion' | 'personal' | 'soporte'`
- [ ] Botón del tab en header con:
  - Icono: `support_agent`
  - Badge contador: `stationTickets().length`
  - Clase activa: `bg-primary/10` cuando `mainTab() === 'soporte'`
  
- [ ] Método `setMainTab('soporte')` que llama `loadSoporte()`
  - `loadSoporte()` → `ticketSvc.loadByStation(resourceId)`

- [ ] Sección HTML del tab (visible cuando `mainTab() === 'soporte'`)
  - Grid 2 columnas: `lg:col-span-1` (soporte) + `lg:col-span-3` (tickets)
  - Estructura vacía de tarjetas para ambas secciones

**Archivo:**
- `frontend/src/app/modules/monitor/resource-monitor.component.ts`

**Aceptación:**
- Tab "Soporte" visible en header
- Click en tab → `loadSoporte()` ejecutado
- Estructura HTML renderizada (sin datos aún)

---

### FASE 4: Frontend — Lista de Tickets

**Objetivo:** Mostrar tickets activos con estados y prioridades

**Tareas:**
- [ ] Renderizar `stationTickets()` en grid de cards
  - Campos: `reference_code`, `title`, `status`, `priority`, `description`
  
- [ ] Badges de estado (colores por status):
  ```
  NEW → rojo/red-400
  ASSIGNED / IN_PROGRESS → azul/blue-400
  PENDING_APPROVAL → ámbar/amber-400
  ```
  
- [ ] Badges de prioridad (colores por priority):
  ```
  CRÍTICA → rojo/red-500
  ALTA → ámbar/amber-500
  MEDIA → azul/blue-500
  BAJA → gris/neutral
  ```
  
- [ ] Estados visuales:
  - `@if (ticketSvc.loadingStation())` → spinner/skeleton
  - `@if (stationTickets().length === 0)` → empty state
  - Botón refrescar: `(click)="loadSoporte()"`

- [ ] Raya de prioridad izquierda (ancho 4px, color por priority)

**Archivo:**
- `frontend/src/app/modules/monitor/resource-monitor.component.ts`

**Aceptación:**
- 3+ tickets mostrados con formato correcto
- Badges de color aplican según spec
- Loading state visible mientras carga
- Empty state visible si sin tickets

---

### FASE 5: Frontend — Acciones Rápidas de Tickets

**Objetivo:** Implementar botones de acción por estado

**Tareas:**
- [ ] Lógica de visibilidad por status:
  ```
  NEW / PENDING_APPROVAL → botón "Asignar"
  ASSIGNED / IN_PROGRESS → botón "Resolver"
  Todos los status → botones "Comentar" + "Escalar"
  ```
  
- [ ] Botones con iconos:
  - Asignar: `assignment_ind` + fondo azul/blue-500
  - Resolver: `check` + fondo verde/emerald-500
  - Comentar: `comment` + fondo neutro/surface
  - Escalar: `arrow_upward` + fondo ámbar/amber-500
  
- [ ] Stubs de métodos (sin lógica aún):
  ```typescript
  assignTicket(ticket: Ticket) { }
  resolveTicket(ticket: Ticket) { }
  commentTicket(ticket: Ticket) { }
  escalateTicket(ticket: Ticket) { }
  ```

**Archivo:**
- `frontend/src/app/modules/monitor/resource-monitor.component.ts`

**Aceptación:**
- Botón "Asignar" solo visible en NEW/PENDING
- Botón "Resolver" solo visible en ASSIGNED/IN_PROGRESS
- Botones "Comentar" y "Escalar" siempre visibles
- Click en botón no causa error

---

### FASE 6: Backend — Soporte por Área (OPCIONAL)

**Objetivo:** Agrupar soporte por `resource_group`/`production_area` en lugar de recurso individual

**Nota:** Reduce cantidad de registros. Si `production_area` no existe, fallback a `resource_id`.

**Tareas:**
- [ ] En `graphic_service.py`, cambiar lógica de `support_members()`
  - En lugar de: `mes_resources.id == resource_id`
  - Hacer: `mes_resources.production_area_id == resource.production_area_id`
  
- [ ] Verificar que `ResourceRead` incluya `production_area_id`

**Archivo:**
- `backend/mes_service/mes_app/services/graphic_service.py`

**Aceptación:**
- GET `/resources/{code}/graphic` retorna soporte por área
- Sin duplicados si hay múltiples recursos en el área

---

### FASE 7: Frontend — Equipo de Soporte

**Objetivo:** Mostrar equipo de soporte del área

**Tareas:**
- [ ] Cargar `supportMembers()` desde `svc.resource()?.support_members`
  - Ya embebido en respuesta de `GET /resources/{code}/graphic`
  
- [ ] Renderizar lista de miembros:
  - Badge con inicial del rol (fondo aleatorio consistente)
  - Mostrar: `collaborator_id` truncado (8 chars) + `role`
  - Botón "Chat" con icono (stub)
  
- [ ] Estados:
  - Si hay miembros → lista
  - Si vacío → "Sin equipo asignado al área"
  
- [ ] Botón "Nuevo Ticket" debajo:
  - Icono: `add_circle`
  - Stub: `openNewTicket()`

**Archivo:**
- `frontend/src/app/modules/monitor/resource-monitor.component.ts`

**Aceptación:**
- Equipo mostrado si tiene miembros
- Empty state visible si sin miembros
- Botón "Nuevo Ticket" presente y clickeable

---

### FASE 8: Testing e Integración E2E

**Objetivo:** Validar flujo completo

**Tareas:**
- [ ] Test manual en `/monitor/resources/CELDA-58D`:
  1. Tab "Soporte" carga sin errores
  2. Tickets se muestran con badges correctos
  3. Equipo de soporte visible
  4. Botones de acción presentes
  5. Refrescar actualiza lista
  
- [ ] Casos edge:
  - Recurso sin tickets → empty state
  - Recurso sin equipo de soporte → "Sin equipo"
  - Loading state aparece y desaparece
  
- [ ] Consola: 0 errores/warnings

**Criterio de éxito:**
- Tab funcional sin console errors
- Interfaz visual limpia y consistente
- Todas las acciones rápidas tienen stubs

---

## Timeline Estimado

| Fase | Duración | Estado |
|------|----------|--------|
| 1 | ✅ | Backend |
| 2 | 10 min | Service + Types |
| 3 | 15 min | Tab structure |
| 4 | 20 min | Ticket list |
| 5 | 15 min | Quick actions |
| 6 | 10 min | Backend grouping |
| 7 | 15 min | Support team |
| 8 | 10 min | E2E testing |
| **Total** | **95 min** | ~1.5 horas |

---

## Dependencias y Notas

### Backend
- Endpoint `GET /tickets?station_id=X` ✅ funcional (Fase 1)
- Campo `Ticket.station_id` ya existe en modelo
- Endpoint `GET /resources/{code}/graphic` retorna `support_members`

### Frontend
- Angular 19 con Signals (ChangeDetectionStrategy.OnPush)
- TailwindCSS para estilos (grid, colores semánticos)
- ResourceService ya inyectable en componente

### Type Safety
- Asegurar `Ticket` type tiene todos los campos necesarios
- `ResourceRead` incluya `support_members: SupportMemberRead[]`

---

## Archivos Afectados

```
backend/
  tickets_service/
    tickets_app/
      infrastructure/repositories/ticket_repository.py          ✅ DONE
      services/ticket_service.py                                ✅ DONE
      routers/ticket_routes.py                                  ✅ DONE

frontend/
  src/app/
    core/
      models/domain.types.ts                                    → Fase 2
      services/ticket.service.ts                                ✅ DONE (Fase 1)
    modules/
      monitor/
        resource-monitor.component.ts                           → Fases 2-8
```

---

## Deuda Técnica Asociada

Relacionado con:
- **ALTA:** Acciones de tickets (asignar, resolver) — requiere backend handlers
- **MEDIA:** Modal de comentarios para tickets
- **MEDIA:** Integración con dialog drawer (SideDrawerService)
- **BAJA:** Animaciones de transición entre tabs

---

## Próximas Fases (después de 172)

1. **Phase 173:** Implementar handlers backend para ticket actions (PATCH status, assign, etc.)
2. **Phase 174:** Dialog comentarios + modal asignar colaborador
3. **Phase 175:** Notificaciones en tiempo real de nuevos tickets (WebSocket)

