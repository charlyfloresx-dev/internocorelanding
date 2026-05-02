# Tareas Consolidadas - 2026-05-02 (Fases 79 & 80)

## ✅ Completado
1. **Tickets Service - Resiliencia Backend**
   - Resolución de Error 500 en la lectura del JWT por el campo de roles (`user.roles` -> `user.role_names`) en `ticket_routes.py`.
   - Resolución de Error 500 (`UniqueViolationError`) en la creación concurrente de tickets rediseñando el algoritmo de folio (`_generate_ref_code`) a un alcance global con suffijos seguros.
   - Resolución de Error 404 para la carga de técnicos (`technicians/workload`) reubicando la ruta por encima del wildcard de IDs.
   - Refactor de prioridades en el frontend (Spanish a EN-Enum backend).
   - E2E scripts automatizados para el ciclo completo (Login -> Create -> Workload -> Triage).

## ⏳ Pendiente (Próximos Pasos)
1. **Frontend: Detalle de Ticket y Modal de Edición**
   - Implementar el modal de Detalle de Ticket que se abrirá desde el Kanban.
   - Enlazar la mutación de campos operativos: `estimated_time`, `module_origin`, `cost_estimate`.
2. **Frontend: Asignación Visual en Kanban**
   - En la tarjeta del Ticket en el dashboard principal, si está en estado NUEVO, implementar selector rápido (dropdown) o vista lateral que permita elegir un técnico para pasarlo a PENDING_APPROVAL / ASIGNADO usando el backend `/triage`.
3. **Auditoría de Activos (Asset Manager)**
   - Relacionar formalmente el `ticket_id` con el inventario físico mediante los endpoints de consumo de recursos.
