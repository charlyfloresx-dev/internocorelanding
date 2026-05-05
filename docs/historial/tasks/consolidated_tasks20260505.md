# Tareas Consolidadas - 2026-05-05

## Phase 86: Muro de Hierro & Identidad (Backlog Superado)
- [x] Corrección del deadlock de concurrencia de Uvicorn en el contenedor monolito, permitiendo peticiones HTTP cross-service.
- [x] Implementación de Endpoints Internos explícitos para resolver la autorización de roles (HCM) y validación de suscripciones (`SubscriptionGuard`).
- [x] Modificación de `get_company_entitlements` para retornar el `status` y la bandera `readonly`, permitiendo al `Auth Service` generar JWT reactivos.
- [x] Corrección del "Critical Middleware Error" (campo `capacity` residual en esquemas de `Warehouse`).
- [x] Restauración de integridad en registros de auditoría al inyectar UUIDs faltantes (`company_id`, `tenant_id`) en SQL plano.
- [x] Suite de estrés validada con **100% de éxito**, probando bloqueos de suscripción (402) y escapes del administrador (God Mode).
- [x] Creación del **Forensic Manifest** como SSOT de UUIDs determinísticos para facilitar migraciones a la nube.

## Phase 87: Operación de Rescate y Observabilidad (Pendientes)
- [ ] **Subscription Recovery Service (Stripe Sync)**: Servicio de rescate en el arranque que consulta la metadata de clientes en Stripe (CompanyID) y restaura la tabla local `subscriptions` si está vacía.
- [ ] **Webhooks de Stripe (Event Listener)**: Implementación del endpoint para escuchar `invoice.payment_failed` y modificar dinámicamente la DB local a estado `PAST_DUE`.
- [ ] **Dashboard de Auditoría Industrial (Frontend)**: Interfaz de observabilidad cruzando en tiempo real las entidades físicas (RFID) vs virtuales (Web), detectando logs de "Acceso Denegado por Suscripción" generados por la Capa de Seguridad (Muro de Hierro).
