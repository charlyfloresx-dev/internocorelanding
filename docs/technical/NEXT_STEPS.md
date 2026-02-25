# Roadmap: God Mode & User Control (RBAC)

Este documento define los pasos críticos para la siguiente sesión de desarrollo, enfocada en la gobernanza administrativa del sistema InternoCore.

## 👑 God Mode (Subscription Administration)
- [ ] **Lógica de Upgrade/Downgrade:** Implementar los handlers en `subscription_service/app/api/v1/endpoints/admin.py`.
- [ ] **Override de Periodo de Gracia:** Permitir extensiones manuales de la suscripción sin necesidad de pago inmediato (Soporte Técnico).
- [ ] **Bypass Auth:** Confirmar que `X-Admin-Master-Key` funciona independientemente del JWT para restaurar cuentas bloqueadas.
- [ ] **Visor de Auditoría:** Implementar query para `AuditSubscriptionLog` con filtros por `company_id`.

## 🛡️ Control de Acceso (RBAC)
- [ ] **Identidad Enriquecida:**
    - [ ] Actualizar `auth_service` para inyectar el claim `role` basado en la tabla `user_company_roles`.
    - [ ] Mapear `accessible_warehouses` consultando la tabla de sucursales autorizadas.
- [ ] **Refactorización de Master Data:**
    - [ ] Aplicar `SubscriptionGuard('master_data_core')` en todos los routers.
    - [ ] Garantizar que registros globales (`company_id IS NULL`) solo sean editables por `God Mode` o roles `SUPER_ADMIN`.
- [ ] **Frontend Route Guards:**
    - [ ] Crear el guard `HasModuleGuard` en Angular.
    - [ ] Implementar el `IsReadonlyGuard` para deshabilitar formularios de edición globalmente.

## 🔍 Trazabilidad & Monitoreo
- [ ] **Cross-Log Search:** Estandarizar el rastro del `correlation_id` para que el error 403 muestre siempre el mismo ID que se guarda en el backend para soporte.
