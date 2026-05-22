# How-To: Configurar Grupos de WhatsApp en InternoCore

Guía para descubrir JIDs de grupos de WhatsApp y registrar `WhatsAppGroupMapping`
para enrutar notificaciones de planta (tickets, alertas de stock, Andon) a grupos específicos.

---

## Arquitectura del flujo

```
Evento de planta
  └─→ notification_service (dispatch matrix)
        └─→ LocalWhatsAppClient.send_group_message(group_name, msg)
              └─→ WhatsAppClientFactory → busca WhatsAppGroupMapping por group_name
                    └─→ gateway Node.js → POST /send → grupo @g.us
```

El campo clave es `group_name` (nombre lógico interno) ↔ `whatsapp_group_id` (JID del grupo).

---

## Paso 1 — Requisito previo: sesión CONNECTED

La sesión debe estar activa antes de poder descubrir grupos.

**Opción A — Desde el panel Angular** (recomendado):
1. Abre el portal como `admin`
2. Menú lateral → **Administración → WhatsApp Gateway** (abre el drawer)
3. Si el estado no es CONNECTED, clic en **"Iniciar y generar QR"** y escanea

**Opción B — Verificar vía script**:
```powershell
cd c:\API\interno
python backend/tickets_service/scripts/test_whatsapp_send.py
# Si dice CONNECTED → continúa. Si dice NOT_INITIALIZED → ve al Paso A.
```

---

## Paso 2 — Descubrir los grupos disponibles

El número de WhatsApp vinculado debe **ya estar en el grupo** que quieres registrar.
Si no está, pídele a un administrador del grupo que te añada primero.

### Desde el panel Angular (UI integrada)

1. Abre el drawer **WhatsApp Gateway** → estado CONNECTED
2. Clic en el botón **"Descubrir grupos"** (lupa verde)
3. Se cargan todos los grupos donde está el número, con su JID y número de participantes

### Desde la terminal (script)

```powershell
python backend/tickets_service/scripts/test_whatsapp_chats.py
```

Output esperado:
```
  JID                                 Participantes  Nombre
  -------------------------------------------------------------------
  120363xxxxxxxxxxxxxxxxx@g.us        12             Técnicos Planta TJ
  120363yyyyyyyyyyyyyyyyy@g.us         5             Supervisores Línea 2
  120363zzzzzzzzzzzzzzzzz@g.us         3             Admin InternoCore
```

---

## Paso 3 — Registrar el mapping

Asigna un **nombre lógico** (`group_name`) al JID del grupo. Este nombre es el que
se usa en el código para enrutar notificaciones (`"TECNICOS_PLANTA"`, `"SUPERVISORES"`, etc.).

### Desde el panel Angular

1. En la lista de grupos descubiertos, localiza el grupo que quieres registrar
2. Clic en **"+ Registrar"**
3. Se muestra un campo de texto con el nombre sugerido (auto-generado del nombre del grupo)
4. Edita si es necesario (solo mayúsculas y guiones bajos, ej: `TECNICOS_PLANTA`)
5. Clic en **OK** o presiona `Enter`
6. El grupo aparece en la sección **"Mappings registrados"** con badge `Activo`

### Desde la terminal (script)

```powershell
python backend/tickets_service/scripts/test_whatsapp_chats.py `
  --register TECNICOS_PLANTA "120363xxxxxxxxxxxxxxxxx@g.us" `
  --display-name "Técnicos Planta TJ"
```

### Desde curl (API directa)

```bash
# Requiere JWT con scope admin
curl -X POST http://localhost:8000/api/v1/whatsapp/mappings \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "TECNICOS_PLANTA",
    "whatsapp_group_id": "120363xxxxxxxxxxxxxxxxx@g.us",
    "display_name": "Técnicos Planta TJ"
  }'
```

---

## Paso 4 — Verificar que el mapping funciona

Envía un mensaje de prueba al grupo usando su JID directamente:

```powershell
python backend/tickets_service/scripts/test_whatsapp_send.py `
  --to "120363xxxxxxxxxxxxxxxxx@g.us" `
  --msg "Prueba de canal grupal InternoCore ✅"
```

Confirma en el grupo de WhatsApp que el mensaje llegó.

---

## Paso 5 — Integrar con la Dispatch Matrix (notificaciones automáticas)

Una vez registrado el mapping, el `LocalWhatsAppClient` lo usa automáticamente.
Para enviar a un grupo desde código:

```python
# En cualquier servicio vía notification_service
await notification_service.send_whatsapp_group(
    db=db,
    company_id=company_id,
    group_name="TECNICOS_PLANTA",   # ← el group_name registrado
    message="🔧 Ticket #TKT-2026-0042 asignado a tu área"
)
```

---

## Nombres lógicos recomendados

| group_name | JID registrado | Propósito |
|---|---|---|
| `ALERTAS_INTERNO` | `120363425542705784@g.us` | Alertas generales de planta (activo) |
| `TECNICOS_PLANTA` | — | Alertas de tickets de mantenimiento |
| `SUPERVISORES` | — | Notificaciones de Andon / paro de línea |
| `ALMACEN` | — | Alertas de stock mínimo / reorden |
| `ADMIN` | — | Notificaciones críticas de sistema |
| `CALIDAD` | — | Alertas de rechazo / no conformidad |

---

## Troubleshooting

| Problema | Causa | Fix |
|---|---|---|
| "Descubrir grupos" no muestra nada | La sesión reconectó pero `getChats()` tarda | Espera 10s y vuelve a intentar |
| El grupo aparece pero no recibe mensajes | El JID cambió (grupos pueden regenerar JID al cambiar dueño) | Re-descubre y actualiza el mapping |
| Error al registrar: "duplicate key" | El `group_name` ya existe para ese tenant | Usa un nombre diferente o actualiza via API (`PATCH /whatsapp/mappings/{id}`) |
| Sesión se desconecta al enviar a grupo | El número fue removido del grupo | Re-añade el número al grupo de WhatsApp |
