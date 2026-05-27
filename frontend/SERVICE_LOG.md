# Service Log — Frontend Angular (interno-web)

## 🕒 Última Actividad (2026-05-27)
**Phase 147: Multi-Tenant Timezone Integration (Frontend)** ✅
- **`local-date.pipe.ts`**: Creado pipe standalone `| localDate` que utiliza `AuthService.companyTimezone()` y `date-fns-tz` para formatear fechas dinámicamente según el timezone del tenant activo. Reemplaza al pipe `date` nativo de Angular que no soporta offsets dinámicos.
- **`auth.service.ts`**: Expuesto `companyTimezone` como un Signal computado leyendo la propiedad `timezone` extraída del JWT del tenant activo (valor inyectado durante el handshake backend).
- **`domain.types.ts`**: Actualizado modelo de autenticación para soportar la lectura segura del timezone en la app de Angular.
- **Migración Progresiva**: Inicio de la sustitución del pipe de fechas nativo `| date` al nuevo `| localDate` a lo largo de componentes críticos como `tickets-form`, `tickets-dashboard` e `inventory-documents`.
- **Status**: ✅ COMPLETED — Base timezone operativa, sustitución progresiva de pipes en curso.

---

**Phase 143: Multi-Asignados Reales + datetime Fecha+Hora en CAPA** ✅

- **`support.types.ts`**: Nuevos tipos `TicketAssignee`, `AssigneeInput`. `Ticket` interface ahora incluye `assignees?: TicketAssignee[]` y `actions?: TicketAction[]`.
- **`support.service.ts` — `triageTicket()` refactorizado**: Nueva firma `(ticketId, action, assignees: AssigneeInput[], comment?)`. Envía lista completa de asignados al backend. Firma vieja eliminada.
- **`tickets-form.component.ts` — `_prePopulateAssignment`**: Lee de `ticket.assignees[]` (tabla nueva). Fallback a 3 columnas legacy si lista vacía. Soporta N asignados de cualquier tipo.
- **`tickets-form.component.ts` — `submitTriage`**: Construye `assignees[]` desde todos los chips de `selectedIdentities()` con `is_lead: idx === 0`. Sin límite de tipo.
- **`tickets-form.component.ts` — datetime CAPA**: Input `type="date"` + `type="time" step="300"` separados. Hora salta de 5 en 5 minutos. `newActionTime` signal para limpiar al crear. Display actualizado a `'d MMM, HH:mm'`.
- **`tickets-dashboard.component.ts` — `getAssignedLabels`**: Lee de `ticket.assignees[]`. Fallback legacy. Soporta N chips por ticket en columna EN PROCESO del kanban.
- **`ticket-triage-drawer.component.ts`**: Migrado a nueva firma `triageTicket(id, action, assignees[])`.
- **`industrial-flows.component.ts`**: Migrado a nueva firma.
- **Status**: ✅ COMPLETED — Multi-asignados operativos. N usuarios del mismo tipo soportados. datetime con paso 5 min.

---

**Phase 142: Tickets — Loop Fix + Multi-Assignees Kanban + TicketActions UI** ✅

- **Angular Signals loop infinito resuelto (`tickets-form.component.ts`)**: Root cause: `_syncIds()` leía `selectedIdentities()` sin `untracked()` dentro del efecto del `SideDrawerComponent`. Ese efecto trackea `drawerService.component()` y `drawerService.data()` — cualquier signal leído síncronamente desde `set data(val)` → `_prePopulateAssignment()` → `_syncIds()` se convierte en dependencia reactiva. Cuando `loadUsersMap()` actualizaba chips async, el efecto re-corría → destruía/recreaba el form → `ngOnInit` → `loadUsersMap()` de nuevo → loop. Fix: `untracked(() => this.selectedIdentities())` en `_syncIds()`. Ya existía `untracked()` en `userMap()` pero faltaba este.
- **`ngOnInit` ya no fetchea lista completa en modo triage**: `loadTickets()` solo corre cuando `view() !== 'triage'`. El setter `set data(val)` prepobla la vista antes de que `ngOnInit` dispare (ciclo Angular: constructor → data setter → ngOnInit), así que la vista ya está en `'triage'` al llegar a `ngOnInit`.
- **Multi-chip responsables en kanban (`tickets-dashboard.component.ts`)**: Columna EN PROCESO mostraba solo `assigned_to_id`. Nuevo método `getAssignedLabels(ticket)` devuelve chips para los tres tipos de identidad (INTERNAL amber, PLANTA teal, EXTERNO purple) con badge de color. Si ninguno asignado muestra "PENDIENTE".
- **Sección "PLAN DE ACCIONES" en drawer triage**: Columna izquierda del SideDrawer de triage incluye lista de `TicketAction[]` con checkbox de cierre, badge de responsable (tipo + nombre) y fecha compromiso. Formulario desplegable para crear nueva acción (descripción + fecha commit). Signals: `actions`, `isLoadingActions`, `isAddingAction`, `newActionText`, `newActionDate`, `showActionForm`. Métodos: `loadActions(ticketId)`, `addAction()`, `closeAction(action)`, `actionAssigneeLabel(action)`.
- **`support.types.ts`**: Nuevo tipo `TicketAction` con todos los campos del backend.
- **`support.service.ts`**: Tres nuevos métodos — `getActions(ticketId)`, `createAction(ticketId, payload)`, `closeAction(ticketId, actionId)`.
- **Status**: ✅ COMPLETED — Loop resuelto. Kanban muestra todos los asignados. Acciones CAPA operativas (requiere rebuild de `tickets-service` para aplicar migración `003_add_ticket_actions`).

---

## 🕒 [2026-05-18] Phase 112: RBAC Frontend — isReadOnly Fix, Kiosk Scopes, Permission Guard ✅

- **`auth.service.ts` — Bug `isReadOnly` extirpado**: `isReadOnly` ya no evalúa `.includes('read')` sobre la lista de permisos. Con slugs granulares como `inventory.stock.read`, el check previo clasificaba a todos los colaboradores como solo-lectura, deshabilitando botones de acción. Ahora depende exclusivamente de `session().readonly` (JWT flag) + estado de suscripción `RESTRICTED` + rol explícito `viewer`.
- **`auth.service.ts` — `isSuperAdmin` endurecido**: Reemplazado `.includes('admin')` (que matcheaba `admin.user.manage`, escalando managers a super-admin) por comparación exacta `r === 'admin' || r === 'owner'` más `permissions.includes('*')`.
- **`auth.service.ts` — `collaboratorLogin()` Case B**: Eliminado el hardcode `permissions: ['inv:movements:manage']`. Ahora lee `data.scopes || data.permissions` del response del backend, propagando los 5 slugs granulares reales del rol `collaborator`.
- **`navigation.service.ts` — Blueprint migrado a slugs DB**: Permisos del menú transaccional actualizados: `inventory` → `inventory.stock.read`, `wms` → `inventory.put_away / inventory.cycle_count`, `catalog` → `master_data.product.write`. `isAdmin()` usa match exacto de rol o `permissions.includes('*')`.
- **`permission.guard.ts` creado**: `CanActivateFn` funcional (`core/guards/permission.guard.ts`). Lee `route.data['requiredPermission']` (string o array OR-semantics). Bypass wildcard `["*"]`. Redirige a `/dashboard` si denegado.
- **`app.routes.ts` — Rutas protegidas**: `/admin/*` → `admin.user.manage`, `/catalog/*` → `['master_data.product.write', 'master_data.product.read']`, `/inventory/audit` → `inventory.audit.view`. TypeScript sin errores de compilación.
- **Status**: ✅ COMPLETED — Menú y rutas alineados con slugs RBAC. Colaboradores no pueden navegar por URL a secciones administrativas.

---

## [2026-05-17] Phase 110 & 111: Navigation Shell, Price Drawer & Dynamic Currency

- **Navigation Shell**: `setup_screen.dart` redirige a `MainNavigationScreen` en restauración de sesión.
- **Price Drawer 750px**: 4 triggers en `product-catalog.component.ts` con `width: 'md:w-[750px] w-full'`.
- **Dynamic Currency**: `product_service.py` `lookup_product_by_code()` resuelve moneda desde `PriceAgreement → ProductPrice → fallback "MXN"`.
- **Status**: ✅ COMPLETED.
