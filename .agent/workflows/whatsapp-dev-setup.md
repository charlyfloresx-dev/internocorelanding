# InternoCore: WhatsApp Dev Setup Protocol

Este flujo de trabajo permite levantar rápidamente el entorno de desarrollo para probar notificaciones de WhatsApp y el Webhook de descubrimiento.

## Paso 1: Levantar el Backend (Notification Service)
Abre una terminal en la raíz del backend del servicio y ejecuta el servidor.
// turbo
```powershell
cd backend/notification_service
$env:PYTHONPATH=".;..;../master_data_service"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Paso 2: Crear el Túnel Público (Localtunnel)
En una **segunda terminal**, expón el puerto 8000 a internet para que Twilio pueda enviarte mensajes.
// turbo
```powershell
npx localtunnel --port 8000
```
> **IMPORTANTE:** Copia la URL que te genere (ej: `https://slight-goats-jump.loca.lt`).

## Paso 3: Configurar Twilio
1. Ve a tu [Twilio Console > Messaging > Sandbox Settings](https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox).
2. En el campo **"WHEN A MESSAGE COMES IN"**, pega tu URL del túnel seguida de `/api/v1/whatsapp/webhook`.
   * Ejemplo: `https://slight-goats-jump.loca.lt/api/v1/whatsapp/webhook`
3. Haz clic en **Save**.

## Paso 4: Validar Conectividad
Envía un mensaje con el texto `/getid` a tu número de Sandbox desde WhatsApp.
* Deberías ver el payload en la terminal del Paso 1.
* El sistema te responderá con tu ID de usuario o grupo.

## Troubleshooting
* **Error 422:** Asegúrate de que el túnel esté activo y la URL en Twilio termine en `/webhook`.
* **Error 429:** Has alcanzado el límite de 5 mensajes diarios del Sandbox de Twilio. Espera 24h o añade crédito.
