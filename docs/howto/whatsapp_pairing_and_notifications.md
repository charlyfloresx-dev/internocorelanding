# How-To: Emparejar WhatsApp y Enviar Notificaciones

**Módulo:** `notification_service` + `whatsapp_gateway`  
**Última actualización:** 2026-05-22  
**Arquitectura:** Gateway Local Multitenant (Puppeteer + whatsapp-web.js) + FastAPI Proxy (ADR-02)

---

## Visión General del Flujo

```
Angular UI (/admin/whatsapp)
     │
     ▼ JWT (company_id aislado)
Nginx :8000  /api/v1/whatsapp/*
     │
     ▼
notification_service :8009  (whatsapp_routes.py — Proxy Espejo ADR-02)
     │
     ▼ Bearer API_KEY
whatsapp_gateway :3011  (Node.js — manager.ts — Singleton + CompanyQueue)
     │
     ▼ whatsapp-web.js (Puppeteer headless)
WhatsApp Web (sesión persistida en volumen Docker)
```

> **Aislamiento multitenant:** el `company_id` se extrae **exclusivamente** del JWT verificado.
> Ningún cliente puede consultar ni alterar la sesión de otro tenant.

---

## Paso 1 — Levantar el Gateway

```powershell
# Desde la raíz del repo
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d --build whatsapp-gateway

# Verificar inicio correcto
docker logs interno-whatsapp-gateway-dev --tail 5
# Esperado: 🚀 InternoCore WhatsApp Gateway running on port 3000
```

---

## Paso 2 — Emparejar la Sesión (Scan QR)

### Opción A: Desde el Portal Angular (recomendado)

1. Inicia el frontend: `cd frontend && npm run start`
2. Entra como `admin` → **Administración → WhatsApp Gateway**
3. Haz clic en **"Iniciar y generar QR"**
4. En tu teléfono: **WhatsApp → Ajustes → Dispositivos vinculados → Vincular dispositivo**
5. Escanea el código QR que aparece en pantalla
6. Espera ~10 segundos → el panel muestra **CONECTADO** (badge verde)

### Opción B: Directo al Gateway (dev/debug)

```powershell
# Inicializar sesión para una empresa concreta
curl -X POST http://localhost:3011/api/v1/whatsapp/session/{COMPANY_ID}/initialize `
  -H "Authorization: Bearer DEV_INTERNAL_KEY_123"

# Consultar QR (estado QR_READY)
curl http://localhost:3011/api/v1/whatsapp/session/{COMPANY_ID}/qr `
  -H "Authorization: Bearer DEV_INTERNAL_KEY_123"
# Respuesta: { qrCode: "data:image/png;base64,..." }
```

### Persistencia de sesión

La sesión se almacena en el volumen Docker `docker_whatsapp_sessions_dev`.  
**Sobrevive reinicios del contenedor.** Si el QR expira, vuelve a hacer clic en "Iniciar y generar QR".

---

## Paso 3 — Probar Envío a un Número Individual

### Opción A: Via API con JWT (recomendado — pasa por todo el stack)

```powershell
# 1. Obtener JWT (login como admin)
$TOKEN = (curl -s -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"charly@interno.com","password":"charly123"}' | ConvertFrom-Json).data.access_token

# Si hay múltiples empresas, hacer select-company primero
# (el portal Angular lo hace automáticamente al elegir la empresa)

# 2. Enviar mensaje de prueba
curl -X POST http://localhost:8000/api/v1/whatsapp/test-send `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"to": "+526641667684", "message": "Prueba InternoCore WhatsApp ✅"}'
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "data": { "status": "success", "message": "Message enqueued successfully." }
}
```

### Opción B: Directo al Gateway (bypass total — solo dev)

```powershell
curl -X POST http://localhost:3011/api/v1/whatsapp/send `
  -H "Authorization: Bearer DEV_INTERNAL_KEY_123" `
  -H "Content-Type: application/json" `
  -d '{"company_id": "<COMPANY_UUID>", "to": "+526641667684", "message": "Test directo"}'
```

> **Formato del campo `to`:**  
> - Número individual: `+526641667684` o `526641667684` → normalizado automáticamente a `526641667684@c.us`  
> - Grupo de WhatsApp: `1234567890-1234567890@g.us` (JID nativo de WhatsApp)

---

## Paso 4 — Configurar Grupos de WhatsApp

Los grupos permiten enrutar notificaciones por área operativa (Técnicos, Supervisores, Admin).

### 4.1 Obtener el JID del grupo

1. El número vinculado debe ser miembro del grupo de WhatsApp
2. Revisar los logs del gateway después de que el número reciba un mensaje en el grupo:
   ```powershell
   docker logs interno-whatsapp-gateway-dev --follow
   # Los mensajes entrantes muestran el chatId: "XXXXXXXXXXXXXXXXXX@g.us"
   ```
3. Alternativamente, usar la consola del gateway para listar chats (pendiente endpoint `/chats`)

### 4.2 Registrar el Mapping de Grupo

```powershell
curl -X POST http://localhost:8000/api/v1/whatsapp/mappings `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    "group_name": "TECNICOS_PLANTA",
    "whatsapp_group_id": "1234567890-9876543210@g.us",
    "display_name": "Técnicos Planta Tijuana"
  }'
```

**Nombres lógicos recomendados:**

| group_name | Propósito |
|---|---|
| `TECNICOS_PLANTA` | Alertas de mantenimiento y fallas |
| `SUPERVISORES` | Escalamientos de SLA |
| `ADMIN` | Auditoría y eventos críticos |
| `LOGISTICA_MX` | Órdenes de transferencia MX |
| `LOGISTICA_US` | Órdenes de transferencia US |

### 4.3 Listar Mappings Activos

```powershell
curl http://localhost:8000/api/v1/whatsapp/mappings `
  -H "Authorization: Bearer $TOKEN"
```

---

## Paso 5 — Integración con el Sistema de Notificaciones

El `notification_service` selecciona automáticamente el canal correcto según la configuración del tenant en `company_notification_configs`.

### Flujo de Dispatch

```
Ticket Worker / Event Source
    │
    ▼ POST /api/v1/events
notification_service (event_routes.py)
    │
    ▼ Dispatch Matrix (prioridad HIGH → IN_APP + EMAIL + WHATSAPP)
WhatsAppClientFactory.get_client_for_tenant(db, company_id)
    │ consulta company_notification_configs (provider = "local" | "twilio")
    ▼
LocalWhatsAppClient.send_group_message(group_id, message, metadata={"company_id": ...})
    │
    ▼ POST /api/v1/whatsapp/send (gateway interno)
whatsapp-gateway:3000
```

### Configurar el Proveedor del Tenant

```sql
-- En notification_service DB (dbname shared)
INSERT INTO company_notification_configs
  (company_id, provider, is_active)
VALUES
  ('<COMPANY_UUID>', 'local', true)
ON CONFLICT (company_id) DO UPDATE SET provider = 'local', is_active = true;
```

O bien vía `.env` como fallback global:
```env
DEFAULT_WHATSAPP_PROVIDER=local
LOCAL_WHATSAPP_GATEWAY_URL=http://whatsapp-gateway:3000
WHATSAPP_GATEWAY_API_KEY=DEV_INTERNAL_KEY_123
```

---

## Paso 6 — Verificación del Stack Completo

```powershell
# Estado del contenedor
docker ps --filter name=interno-whatsapp-gateway-dev

# Logs en tiempo real
docker logs interno-whatsapp-gateway-dev --follow

# Estado de la sesión via API
curl http://localhost:8000/api/v1/whatsapp/session/status `
  -H "Authorization: Bearer $TOKEN"
# Esperado: { "status": "success", "data": { "status": "CONNECTED" } }
```

---

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| QR no aparece / spinner infinito | Gateway no corriendo | `docker logs interno-whatsapp-gateway-dev` |
| `503 WhatsApp Gateway unreachable` | URL incorrecta en `.env` | Verificar `LOCAL_WHATSAPP_GATEWAY_URL=http://whatsapp-gateway:3000` |
| Sesión muestra `FAILED` | Chromium crasheó sin `--no-sandbox` | Revisar args de Puppeteer en `manager.ts` |
| `401 Unauthorized` al llamar al gateway | API key incorrecta | `WHATSAPP_GATEWAY_API_KEY` debe coincidir con `API_KEY` en gateway |
| Mensaje encolado pero no llega | Número no en `@c.us` o sesión desconectada | Verificar estado `CONNECTED` y formato del número |
| QR expiró antes de escanear | Tiempo límite de WhatsApp (~60s) | Hacer clic en "Iniciar y generar QR" nuevamente |

---

## Variables de Entorno Requeridas

| Variable | Servicio | Valor en dev |
|---|---|---|
| `LOCAL_WHATSAPP_GATEWAY_URL` | notification_service | `http://whatsapp-gateway:3000` |
| `WHATSAPP_GATEWAY_API_KEY` | notification_service | `DEV_INTERNAL_KEY_123` |
| `DEFAULT_WHATSAPP_PROVIDER` | notification_service | `local` |
| `PORT` | whatsapp_gateway | `3000` |
| `API_KEY` | whatsapp_gateway | `DEV_INTERNAL_KEY_123` |
| `SESSIONS_PATH` | whatsapp_gateway | `/app/sessions` |
