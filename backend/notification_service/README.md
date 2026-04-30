# 🔔 Notification Service (Puerto 8010)

El **Notification Service** es el **bus de comunicaciones** de Interno Core. Gestiona el envío de correos transaccionales, invitaciones a plataforma y alertas operativas a través de múltiples canales (Email/Resend, WhatsApp/Twilio).

---

## 🏗️ Responsabilidades del Dominio

- **Email Transaccional**: Envío mediante Resend API (invitaciones, reseteo de contraseña, alertas de suscripción).
- **WhatsApp Business**: Notificaciones industriales a grupos y contactos vía Twilio Sandbox/API.
- **Webhook Discovery**: Mapeo de grupos de WhatsApp a unidades de negocio (`company_id`).
- **Broadcasting**: Emisión de alertas multi-destinatario para paros de línea, mantenimiento urgente, etc.
- **Plantillas**: Sistema de plantillas HTML/texto reutilizables por tipo de notificación.

---

## 🔗 Integraciones (Inbound — Recibe eventos de)

| Emisor | Evento |
|--------|--------|
| **Auth Service** | Invitación de nuevo usuario a plataforma |
| **HCM** | Alerta de certificación por vencer |
| **MES** | Paro de línea o desviación de OEE |
| **CMMS** | Orden de mantenimiento urgente |
| **Subscription** | Aviso de vencimiento de licencia |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/dbname
RESEND_API_KEY=...
CORE_RESEND_API_KEY=...
CORE_TWILIO_ACCOUNT_SID=...
CORE_TWILIO_AUTH_TOKEN=...
CORE_WHATSAPP_SENDER_NUMBER=whatsapp:+14155238886
```
