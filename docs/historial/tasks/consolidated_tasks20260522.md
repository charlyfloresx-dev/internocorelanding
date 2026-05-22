# Consolidado de Tareas: 2026-05-22

Jornada de verificación y documentación: Phase 124 — WhatsApp E2E Verification + Test Send Endpoint + How-To Docs.

---

## Phase 124 — WhatsApp E2E Verified + Test Send Endpoint + Documentación ✅ COMPLETADO

### Verificación E2E (sesión conectada)

- `[x]` Sesión WhatsApp escaneada desde `/admin/whatsapp` → estado **CONNECTED** confirmado en UI Angular.
- `[x]` Polling `/api/v1/whatsapp/session/status` retorna 200 OK (confirmado en DevTools Network — 101 requests, 991 KB transferidos).
- `[x]` QR Base64 correctamente renderizado como `data:image/png;base64,...` en el panel Angular.

### Endpoint `POST /api/v1/whatsapp/test-send`

- `[x]` `TestWhatsAppMessageRequest` — schema actualizado para incluir campo `to` (número o group JID).
- `[x]` Endpoint `POST /whatsapp/test-send` añadido en `notification_service/app/routers/whatsapp_routes.py`.
  - Protegido con `require_scope(["admin"])` + JWT Iron Wall (company_id del token).
  - Proxy directo a `POST /api/v1/whatsapp/send` en el gateway Node.js.
  - Formato `to`: acepta `+52XXXXXXXXXX` (normalizado automáticamente a `XX@c.us`) o `XXXX@g.us` (grupos).
- `[x]` `notification-service` reconstruido y redesplegado: `docker compose up -d --build notification-service`.

### Documentación How-To

- `[x]` `docs/howto/whatsapp_pairing_and_notifications.md` — guía completa creada:
  - Diagrama de flujo end-to-end (Angular → Nginx → notification_service → gateway → WhatsApp)
  - Paso 1: Levantar el gateway
  - Paso 2: Emparejar la sesión (Opción A portal Angular / Opción B curl dev)
  - Paso 3: Probar envío a número individual (JWT stack completo + bypass dev)
  - Paso 4: Configurar grupos (`WhatsAppGroupMapping` → `group_name` → JID)
  - Paso 5: Integración con Dispatch Matrix (event → LocalWhatsAppClient → gateway)
  - Paso 6: Verificación + Troubleshooting + Variables de entorno

---

## Phase 125 — Sentinel Mobile Ticket Integration & Support Drawer Sync ✅ COMPLETADO

### Capa de Datos (Data Layer)
- `[x]` Crear `ticket_models.dart` con DTOs de `Ticket`, `TicketCreateRequest` y `TicketComment`.
- `[x]` Crear `ticket_repository.dart` con inyección de `company_id` automático desde la sesión local.

### Gestión de Estado (BLoC)
- `[x]` Crear `tickets_bloc.dart` con soporte completo para carga de tickets, creación y visualización de comentarios.
- `[x]` Registrar `TicketsBloc` e inyectarlo en `injection.dart` y `main.dart`.

### Interfaz "Uber-Style" (UI Layer)
- `[x]` Modificar `tickets_screen.dart` para consumir dinámicamente datos reales mediante `TicketsBloc`.
- `[x]` Crear `create_ticket_screen.dart` con formulario express de Nivel 1.
- `[x]` Crear `ticket_chat_screen.dart` con burbujas de chat, auto-scroll y cabecera de datos maestros.

### Aseguramiento estático
- `[x]` Ejecución de `flutter analyze` exitosa con 0 warnings y 0 errores.

---

## Phase 126 — Multi-Tenant Isolated Ticket Consecutive Number Fix ✅ COMPLETADO

### Base de Datos & Migraciones
- `[x]` Crear migración de Alembic `002_ref_code_composite.py` para reemplazar el índice único global en `reference_code` por un índice único compuesto `(company_id, reference_code)`.
- `[x]` Correr la migración dentro del contenedor (`docker exec interno-tickets-dev python -m alembic upgrade head`) de forma exitosa.
- `[x]` Modificar el modelo SQLAlchemy de `Ticket` en `ticket.py` agregando la restricción compuesta a `__table_args__`.

### Lógica de Folios
- `[x]` Refactorizar `_generate_ref_code` en `ticket_repository.py` para contar consecutivamente por empresa y año actual, soportando todos los prefijos.
- `[x]` Validar la continuidad correcta del consecutivo a partir de los registros existentes (ej. genera `TKT-2026-0008` tras los 7 pre-sembrados).

---

## Phase 124 Addendum — WhatsApp Drawer UI + SingletonLock Fix ✅ COMPLETADO

### Drawer deslizable (mismo patrón que POS)
- `[x]` `WhatsAppGatewayComponent` adaptado como drawer: `min-h-screen bg-white p-12` → `p-6`, `max-w-xl` removidos de panels.
- `[x]` `main-layout.component.ts` — ítem "WhatsApp Gateway" en menú admin cambiado de `routerLink="/admin/whatsapp"` a `openWhatsAppGatewayDrawer()`.
- `[x]` `openWhatsAppGatewayDrawer()` implementado con `SideDrawerService.open(WhatsAppGatewayComponent, { width: 'w-[520px]' })`.

### SingletonLock fix (Chromium session persistence)
- `[x]` Root cause identificado: `SingletonLock` es un **symlink** — `fs.existsSync()` seguía el symlink y retornaba `false` para symlinks rotos (socket del contenedor anterior destruido). Cleanup nunca corría.
- `[x]` Fix en `backend/whatsapp_gateway/src/manager.ts`: cleanup usa `fs.lstatSync()` (opera sobre el symlink mismo) antes de cada `initializeSession`. Limpia `SingletonLock`, `SingletonSocket` y `SingletonCookie`.
- `[x]` Gateway reconstruido y redesplegado.

### Verificación de entrega confirmada
- `[x]` **Mensaje recibido físicamente en `+526641667684`** — "InternoCore WhatsApp test - canal local multitenant activo" — 1:44 PM ✓✓.
- `[x]` LID resolution confirmado en logs: `Resolved number +526641667684 -> 263401871777841@lid`.
- `[x]` Stack completo validado: Angular → Nginx:8000 → notification_service:8009 → gateway:3011 → WhatsApp.

---

## Phase 127 — Sentinel Mobile Dashboard Enrichment & Field Alignment ✅ COMPLETADO

### Capa de Datos y Modelos (Mobile)
- `[x]` Enriquecer el DTO `Ticket` en `ticket_models.dart` para incluir `assignedToId`, `area` y `ticketType` mapeados desde JSON.
- `[x]` Cambiar la URL de consulta de tickets a `tickets/mine` en `ticket_repository.dart` para aislar el tablero del operador.

### Interfaz de Usuario (Mobile Dashboard)
- `[x]` Agregar barra lateral de prioridad de color (Crítica = Rojo, Alta = Naranja, Media = Amarillo, Baja = Azul) en `_buildTicketItem` de `tickets_screen.dart`.
- `[x]` Agregar badge de prioridad visual con texto estilizado.
- `[x]` Agregar indicador de asignación ("👤 Asignado" vs "⚠️ Sin Asignar").
- `[x]` Mostrar tag visual con el área operativa del ticket.

### Verificación y Backend
- `[x]` Validar compatibilidad de campos con el DTO `TicketRead` del microservicio `tickets_service`.
- `[x]` Comprobación de integridad del Code Graph (0 errores) y endpoints HMAC (/tickets/internal retornando 403 sin firma).
- `[x]` Ping maestro de servicios vía script `validate_ecosystem.ps1` exitoso.

---

---

## Phase 128 — WhatsApp Group Discovery + Registration UI + E2E Group Delivery ✅ COMPLETADO

### Gateway (Node.js)
- `[x]` `getChats(companyId)` en `manager.ts` — filtra grupos `@g.us`, retorna JID + nombre + participantes.
- `[x]` `GET /api/v1/whatsapp/session/:company_id/chats` en `index.ts`.

### Notification Service
- `[x]` `GET /whatsapp/session/chats` proxy ADR-02 en `whatsapp_routes.py`.

### Frontend Angular (Drawer WhatsApp Gateway)
- `[x]` Botón "Descubrir grupos" → carga lista desde sesión activa con JID y participantes.
- `[x]` Sección "Mappings registrados" → carga automática al entrar en CONNECTED.
- `[x]` Registro inline → input con nombre auto-sugerido, OK / ✕, badge "Registrado".
- `[x]` `FormsModule` añadido al componente standalone.

### Docs
- `[x]` `docs/howto/whatsapp_group_setup.md` — how-to completo de 5 pasos.
- `[x]` `backend/tickets_service/scripts/test_whatsapp_chats.py` — CLI de descubrimiento y registro.
- `[x]` `initialize-dev.md` y `sync-docs.md` actualizados.

### Verificación E2E
- `[x]` Grupo "Coppel" (`120363042693431357@g.us`, 4 participantes) — mensaje recibido físicamente a las 2:22 PM ✓✓.
- `[x]` `ALERTAS_INTERNO` → `120363425542705784@g.us` registrado en DB.

---

## Pendientes (próximas sesiones)

- `[ ]` Rate limiting en endpoints de `subscription_service` y `master_data_service`.
- `[ ]` Fix conocido: `GET /products/{id}/variants` retorna 403 para rol `collaborator` — agregar `inventory:read` al scope mapping en `select_company_command.py`.
- `[ ]` `default_tax_rate` en Planta US debería ser 0.0 (actualmente 0.16).
- `[ ]` Registrar mapping `TECNICOS_PLANTA` con JID del grupo real de técnicos de planta.
