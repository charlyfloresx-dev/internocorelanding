# Consolidated Tasks - 2026-03-20

## 📂 Core: Backend Auth & Multi-Tenancy
- [x] Endpoint `GET /users/` para listado por tenant en `auth_service`.
- [x] Endpoint `POST /users/invite` para generar códigos de invitación.
- [x] Unificar modelos de `Company` en `common`.
- [x] Reemplazar envío directo de correos por delegación al `notification_service`.

## 📂 Infrastructure: Docker & Services
- [x] Añadir `notification-service` al `docker-compose.yml`.
- [x] Reparar Dockerfile del servicio de notificaciones (estaba duplicado del servicio de tickets).
- [x] Corregir dependencias y PYTHONPATH en el contenedor de notificaciones.
- [x] Sincronizar esquemas de DB en `notification_service` (corrección de tipos UUID SQLA).

## 📂 Frontend: Admin Dashboard
- [x] Aplicar estilo "Light Theme" a la tabla de usuarios (`UserManagementComponent`).
- [x] Implementar badges pastel para estados de usuario (Activo, Inactivo, Pendiente).
- [x] Añadir acciones de tabla dinámicas (Edit/Delete).
- [ ] Conectar el modal de "Invitar Usuario" con el nuevo endpoint `/invite`.
- [ ] Paginación de usuarios en el frontend.

## 📂 Backlog / Próximos Pasos
- [ ] Implementar el endpoint para "Aceptar Invitación" (handshake final).
- [ ] Integrar el `NotificationClient` en el proceso de cambio de contraseña.
- [ ] Aplicar el nuevo estilo de tabla en los módulos de `Inventory` y `Billing`.
