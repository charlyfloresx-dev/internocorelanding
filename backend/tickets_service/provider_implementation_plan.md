# Plan de Implementación: Asignación a Proveedores (Tickets Service)

Este plan de implementación cierra el círculo entre el legado administrativo de .NET y la agilidad operativa del nuevo Monolito Unificado en Python. Al fusionar los conceptos de `Contact.cs` y `Person.cs` en un modelo de `ExternalContact` dentro del `common`, garantizamos que la "fuente de verdad" de los proveedores sea accesible no solo para tickets, sino para futuras integraciones de compras o gestión de activos (`cmms_service`).

A continuación, se presenta el desglose técnico dividido por fases para una ejecución y revisión estructurada.

---

## 🏗️ FASE 1: Arquitectura de Datos (Legacy Bridge en Common)
**Objetivo:** Crear los modelos base en `backend/common/models/` para dar soporte a la identidad externa sin consumir licencias internas.

### 1. Reutilización del Modelo `Partner` (Evolución de `Company.cs`)
*   **Arquitectura:** En lugar de crear un modelo `Provider` nuevo, aprovecharemos el modelo `Partner` ya existente en `master_data_service/master_app/models/partner.py`. Este modelo ya hereda de `MultiTenantBase` y posee la estructura requerida (code, name, tax_id, type).
*   **Identidad:** El tipo `PartnerType.BOTH` o `PartnerType.SUPPLIER` nos permite consolidar de forma natural el legacy `Company.cs`.
*   **Eficiencia:** Esto evita la duplicidad conceptual de entidades B2B dentro de InternoCore.

### 2. Modelo `ExternalContact` (Fusión de `Contact.cs` y `Person.cs`)
*   **Aislamiento:** Hereda de `MultiTenantBase`.
*   **Identidad:** Almacena el `full_name` (combinación de FirstName + LastNamePat) y el `email` obligatorio y único por tenant como canal primario de comunicación.
*   **Vínculo Flexible:** Relación N:N con `Partner` mediante una tabla asociativa `partner_contacts`, permitiendo que un contacto externo trabaje para múltiples proveedores.
*   **Rol Operativo:** Campos de `job_title` y `department` para el contexto de la asignación.
*   **Seguridad de Plan:** La capacidad del contacto para subir documentos o evidencia estará condicionada a que el `TenantPlan` de la empresa tenga activa la funcionalidad de "Evidencia Externa".
*   **Contacto Adicional:** `phone` para emergencias operativas.

---

## 🚦 FASE 2: Extensión del Dominio Tickets (Pydantic & CQRS)
**Objetivo:** Adaptar los esquemas y comandos del `tickets_service` para soportar asignación dual (interna vs. externa).

### 2. Lógica del Ticket y la "Triple Identidad Industrial" (Tickets Service)
Dentro del dominio de Tickets (`backend/tickets_service/tickets_app/`):
*   **Modelo `Ticket`**: Se implementará el soporte para tres tipos de asignación:
    1.  `assigned_to_id`: Usuario digital del sistema (Interno).
    2.  `collaborator_id`: Identidad física/operativa del colaborador (Interno, puede no tener usuario web).
    3.  `external_contact_id`: Contacto externo de un proveedor/partner (Externo, Zero-Consumption).

*   **Flujo de Sub-tareas**: El diseño existente de `parent_ticket_id` se utilizará para modelar el escenario de:
    *   Ticket Padre (Interno, asignado a un Collaborator local).
    *   Sub-tarea (Externo o Interno, asignado a `external_contact_id` o `collaborator_id`).

### 3. Capa CQRS (`CreateTicketCommand`)
*   **Esquemas de Validación (Pydantic)**: La lógica de comando debe validar que se proporcione al menos un destinatario válido.
*   **Invariante de Correo**: Si se usa `external_contact_id`, se exige que dicho contacto tenga un `email` obligatorio (requerido para el Outbox Bridge).
*   **Validación de Plan**: Solo se permitirá asignar a `external_contact_id` si el tenant cuenta con el módulo de "Evidencia Externa" activo.

---

## 🛡️ FASE 3: Persistencia, Eventos y Trazabilidad (Monolito)
**Objetivo:** Modificar el modelo de base de datos del Ticket y establecer el puente de comunicación asíncrona hacia el proveedor.

### 1. Modificación del Modelo SQLAlchemy (`Ticket`)
*   **Nueva Columna:** Agregar `external_contact_id` como `Mapped[Optional[uuid.UUID]]` con una Foreign Key débil o explícita hacia `external_contacts.id`.

### 2. Puente de Comunicación (Outbox Bridge)
*   **Atomicidad:** Al crear o reasignar una sub-tarea a un proveedor, insertar atómicamente un evento `ExternalAssignmentEvent` en la tabla `outbox` dentro de la misma transacción (DBSession). Esto previene "tickets huérfanos" que el proveedor nunca reciba.
*   **Payload del Evento:** El JSON emitido debe contener el `Ticket ID`, el `PrettyName` del contacto y el `Code` del proveedor, listo para ser consumido por el Notification Worker.
*   **Automatización de Notificaciones (Liberación de Carga):** Configurar el flujo de eventos para que, si una sub-tarea se reasigna desde un técnico interno hacia un contacto externo (`external_contact_id`), se dispare automáticamente un evento de "Liberación de Carga" notificando al usuario interno que el ticket ha sido delegado exitosamente al proveedor.

### 3. Auditoría Forense y Licenciamiento
*   **Zero-Consumption:** Al no existir un `user_id` vinculado al contacto externo en las tablas de seguridad (`Auth`), el proveedor no consume una licencia de usuario del tenant, maximizando la eficiencia de costos.
*   **Ledger de Acciones:** Cuando el proveedor interactúe con el ticket (ej. mediante una vista pública o un webhook validado con un token), cualquier cambio de estado (de `NEW` a `IN_PROGRESS`) se registrará en el `AuditService` inyectando la constante `EXTERNAL_PROVIDER_ACTION` en lugar de un ID de usuario. Esto permite diferenciar analíticamente las tareas resueltas internamente de las tercerizadas.

---

## 🏗️ FASE 4: Validaciones Críticas y Blindaje Operativo
**Objetivo:** Asegurar la resiliencia del sistema mediante scripts de validación automatizados para escenarios de excepción y cumplimiento.

### 1. Flujo de Reasignación y Liberación de Carga (`flow_load_balancing.py`)
*   **Validación:** El sistema debe asegurar que al reasignar un ticket de un Usuario Interno a un Proveedor Externo, el campo `assigned_to_id` se limpie (NULL) para liberar la carga del técnico.
*   **Evento:** Verificar la inserción del evento de asignación externa en el Outbox.

### 2. Cumplimiento de SLA y Expiración Forense (`flow_token_expiration.py`)
*   **Validación:** Los enlaces de acceso para proveedores deben expirar estrictamente después de 72 horas.
*   **Seguridad:** Los tokens expirados deben retornar `403 Forbidden` en los endpoints públicos.

### 3. Control de Cuotas de Evidencia (`flow_evidence_quota.py`)
*   **Validación:** Los proveedores están sujetos a las restricciones de `max_upload_size_mb` del tenant.
*   **Integridad:** Bloqueo de subidas que excedan la configuración del plan.

---

## ✅ ESTADO DE EJECUCIÓN (2026-05-08)
*   [x] **FASE 1:** Modelos `Partner` y `ExternalContact` creados en `common`.
*   [x] **FASE 2:** Esquemas de Tickets actualizados para Triple Identidad.
*   [x] **FASE 3:** Migraciones aplicadas (`external_assigned_at`), Semilla Industrial completada.
*   [ ] **FASE 4:** Implementación de Scripts de Validación (En progreso).
*   [ ] **FASE 5:** Desarrollo de Landing Page de Proveedores (Pendiente).
