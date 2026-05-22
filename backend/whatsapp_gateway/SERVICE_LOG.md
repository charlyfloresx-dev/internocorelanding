# WhatsApp Gateway – Log

## Última Actividad (2026-05-22)
**Phase 128: Group Discovery Endpoint + E2E Group Delivery** ✅
- **`src/manager.ts`**: Nuevo método `getChats(companyId)` — `client.getChats()` filtrado a grupos `@g.us`, retorna `{ id, name, participantCount }`.
- **`src/index.ts`**: Nuevo endpoint `GET /api/v1/whatsapp/session/:company_id/chats` — protegido con Bearer, retorna lista de grupos con sus JIDs.
- **E2E verificado**: Mensaje entregado al grupo "Coppel" (`120363042693431357@g.us`, 4 participantes) a las 2:22 PM ✓✓.

## Última Actividad (2026-05-22)
**Phase 124 Addendum: LID Fix + SingletonLock Cleanup + E2E Delivery** ✅
- **`src/manager.ts` — LID Fix**: `CompanyQueue.processNext()` ahora usa `client.getNumberId(cleanNumber)` para resolver el LID antes de `sendMessage()`. Soluciona el error `Error: No LID for user` introducido por el cambio de protocolo de WhatsApp. Para grupos `@g.us` se usa el JID directamente.
- **`src/manager.ts` — SingletonLock Cleanup**: `initializeSession()` limpia `SingletonLock`, `SingletonSocket` y `SingletonCookie` antes de cada inicialización. Root cause: `SingletonLock` es un symlink; `fs.existsSync()` sigue el symlink y retorna `false` para symlinks rotos. Fix: `fs.lstatSync()` que opera sobre el symlink mismo.
- **E2E verificado**: `[Queue] Resolved number +526641667684 -> 263401871777841@lid` → `[Queue] Message successfully delivered to 263401871777841@lid`. Mensaje recibido físicamente.

## Última Actividad (2026-05-22)
**Phase 123: Gateway Deployment + Angular QR UI** ✅
- Contenedor `interno-whatsapp-gateway-dev` desplegado en puerto 3011 (interno: 3000).
- `infrastructure/docker/nginx.conf`: ruta `location /api/v1/whatsapp` añadida → proxy a `notification_service`.
- `frontend/src/app/modules/admin/whatsapp-gateway.component.ts` (NUEVO): Panel QR completo con máquina de estados reactiva (Signals), polling 5s, inicialización desde UI.

## Última Actividad (2026-05-21)
**Phase 121 Fase 2: WhatsApp Local Multitenant Gateway — Node.js microservice** ✅
- `src/manager.ts`: Singleton `WhatsAppSessionManager` + `CompanyQueue` con anti-ban delay 1.5–3s. Sesiones aisladas por `company_id`.
- `src/index.ts`: Express 4 + Bearer auth (`API_KEY`) + 4 endpoints: `POST /initialize`, `GET /status`, `GET /qr`, `POST /send`.
- `Dockerfile`: Node 22 LTS + Chromium headless. Volumen `whatsapp_sessions_dev` para persistencia de `LocalAuth`.
