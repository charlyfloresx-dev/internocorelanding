# InternoCore: Especificaciones Técnicas (Backend & Infraestructura)

## 📋 Rol del Agente
Ingeniero de Backend e Infraestructura. Foco en ecosistema de microservicios y consistencia del Multitenancy.

## 🏗️ Arquitectura y Contexto
- **Arquitectura**: Clean Architecture con CQRS y patrón de microservicios en Python.
- **Multitenancy**: El `company_id` es mandatorio en cada transacción.
- **Autenticación**: Debe retornar `CompanyAccessDto`.
- **SaaS Core**: El backend debe funcionar idéntico en Local (Docker) y AWS.
- **Suscripciones**: Acciones (crear, actualizar, cancelar) deben manejarse vía CQRS (Comandos/Consultas).
- **RBAC Multitenant**: La autorización se basa en `UserCompanyRole`. Los scopes deben fusionar los permisos del Rol y los específicos del usuario en esa empresa.
- **Webhooks de Pago**: El `subscription_service` debe procesar eventos `checkout.session.completed` de Stripe para activación automática y sincronización de periodos (`current_period_end`).
- **Fallos de Pago**: El webhook debe manejar `invoice.payment_failed` para cambiar el estado a `PAST_DUE` y activar el protocolo de "Grace Period".
- **God Mode**: Estado de privilegio elevado volátil. Uso de `x-admin-master-key` para bypass de seguridad y flag `bypass_tenant` en `BaseRepository`. Override de `grace_period_until` en suscripciones.
- **Transferencias Inter-Company**: Implementación de comandos atómicos por tenant. Uso de `TransactionPairId` para vinculación. Orquestación vía Outbox Pattern y Sagas para consistencia distribuida.
- **Herencia Obligatoria**: Movimientos de transferencia deben heredar de `MultiTenantBase` (aislamiento) y `AuditBase` (trazabilidad de autorización).
- **Resiliencia Offline**: La fecha de expiración debe persistirse localmente para no depender de Stripe en cada request.
- **Microservicios**: El `PYTHONPATH` incluye `/app` y la carpeta del servicio.
- **Precios y Stock**: Siempre filtrados por Compañía y Almacén (`warehouse`).

## 🛠️ Reglas de Ejecución Local (VSC / Cursor)
1. **Sin Ejecución Directa**: El agente no debe ejecutar comandos directamente. Debe proporcionar el comando exacto para que el usuario lo ejecute.
2. **Sincronización Frontend**: Cada modificación en el Backend (FastAPI) o esquema de DB (Alembic) requiere generar un resumen del JSON de respuesta para sincronización con el agente de Frontend.
3. **Documentación Continua**: Siempre proveer especificaciones técnicas y prompts de ejecución al solicitar apoyo. Actualizar logs del proyecto inmediatamente.

## 📡 Sincronización JSON (Ejemplos)
*Documentar aquí los modelos de respuesta para el consumo del Frontend.*

- **Auth Handshake**:
  ```json
  {
    "status": "success",
    "data": {
      "selection_token": "T1_TOKEN",
      "available_accesses": [
        {
          "company": { "id": "uuid", "name": "Nombre", "logo": "url" },
          "role": { "id": "uuid", "name": "Admin" }
        }
      ]
    }
  }
  ```

- **Paginación Estándar (Ej. Kardex/Movements)**:
  - **Query Params Requeridos**: `page` (int, default=1), `page_size` (int, default=50).
  - **Estructura de Respuesta**:
  ```json
  {
    "status": "success",
    "data": [
      { "id": "uuid", "amount": 100 }
    ],
    "message": "Data retrieved successfully",
    "meta": {
      "page": 1,
      "page_size": 50,
      "total_records": 1200,
      "total_pages": 24
    }
  }
  ```
