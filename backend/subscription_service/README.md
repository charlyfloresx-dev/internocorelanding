# 🔑 Subscription Service (Puerto 8002)

El **Subscription Service** es el **motor de licenciamiento** de Interno Core. Gestiona los planes de suscripción, el estado de las licencias por empresa y el control de acceso a módulos (`modules` claim en JWT), operando como el "God Mode" del ecosistema.

---

## 🏗️ Responsabilidades del Dominio

- **Planes de Suscripción**: Free, Starter, Professional, Enterprise con módulos habilitados por plan.
- **Licencias por Empresa**: Estado activo/vencido/suspendido por `company_id`.
- **Control de Módulos**: Determina qué módulos (`wms`, `mes`, `hcm`, etc.) están habilitados en el JWT.
- **Modo Lectura (`readonly`)**: Bloquea escrituras automáticamente si la suscripción está vencida.
- **Kill Switch**: Desactivación inmediata de acceso a nivel plataforma para gestión de impagos.
- **Integración con Stripe**: Gestión de pagos y webhooks de facturación.

---

## 🔗 Integraciones

| Servicio | Propósito |
|----------|-----------|
| **Auth** | Inyecta `modules` y `readonly` en el payload JWT final (T2) |
| **Notification** | Dispara avisos de vencimiento y confirmaciones de pago |
| **Stripe** | Webhooks de `payment_succeeded` y `subscription_cancelled` |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/subscription_db
CORE_SECRET_KEY=...
SECRET_KEY=...
CORE_STRIPE_SECRET_KEY=...
CORE_STRIPE_WEBHOOK_SECRET=...
CORE_STRIPE_PRODUCT_ID=...
```
