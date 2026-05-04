# Tareas Consolidadas - 2026-05-04

## Backlog Superado
- [x] Migración del dominio de `WorkOrder` hacia el kernel compartido (`common/models/work_order_base.py`).
- [x] Refactorización de la base de datos de CMMS a múltiples archivos para escalabilidad (`asset.py`, `work_order.py`, `tool.py`, etc.).
- [x] Desacoplamiento de variables Enum quemadas hacia la nueva tabla de catálogos `Enumeration` (Master Data).
- [x] Script de sincronización de Enums (`sync_enums.py`).
- [x] Auditoría del Módulo CMMS documentando deltas.

## Pendientes / Deltas Identificados
- [ ] Implementar endpoint `POST /consume` en `work_order_routes.py` para consumibles.
- [ ] Orquestación asíncrona de eventos de Dominio (`ToolCheckout`, `ConsumableUsed`) hacia el `inventory_service`.
- [ ] Desarrollo de UI/UX en el frontend (Kanban de Mantenimiento y Dashboard unificado).
- [ ] **Phase 86**: Generar migración Alembic para la tabla `security_audit_logs`.
- [ ] **Phase 86**: Inyectar evento de auditoría en `collaborator_login_command.py` (`auth_service`).
- [ ] **Phase 86**: Habilitar endpoint unificado `/api/v1/core/identity/search` para consolidación User/Collaborator.

## Phase 86: Backlog Superado
- [x] Creación del modelo `SecurityAuditLog` en `common/models`.
- [x] Adición de `user_id` a `Collaborator` en `hcm_service`.
