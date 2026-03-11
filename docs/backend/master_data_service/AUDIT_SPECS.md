# Especificaciones de Auditoría: Master Data Service

**Fecha:** 2026-02-14
**Versión:** 3.0 (Motor de Auditoría Pro - SSOT)
**Alcance:** Implementación de un Libro Mayor Inmutable (Immutable Ledger) para trazabilidad forense completa.

## 1. Arquitectura del Ledger de Auditoría

El sistema implementa un ledger centralizado a través de la tabla `audit_logs`. Esta tabla actúa como la Fuente Única de Verdad (SSOT) para todos los cambios de estado en el sistema. La captura de datos es automática y no intrusiva, gracias a un sistema de middleware y eventos de base de datos.

### Pilares de la Arquitectura:
1.  **Middleware de Contexto (`AuditMiddleware`):** Intercepta todas las peticiones para extraer/generar un `X-Correlation-ID` y capturar el contexto de la petición (`client_ip`, `user_agent`).
2.  **Event Listeners de SQLAlchemy:** Se enganchan al ciclo de vida de la sesión de la base de datos (`before_flush`) para inspeccionar los objetos modificados (`session.new`, `session.dirty`, `session.deleted`).
3.  **Modelo `AuditLog`:** Entidad centralizada que almacena el "antes" y "después" de cada cambio, junto con todo el contexto de la transacción.

## 2. Flujo de Trazabilidad (Correlation ID)
- El Frontend DEBE enviar un `X-Correlation-ID` (UUID v4) en las cabeceras de las peticiones que componen una transacción de negocio.
- Si el header no está presente, el `AuditMiddleware` generará uno y lo devolverá en la respuesta para que el cliente pueda continuar la traza.
- Este `correlation_id` se guarda en cada registro de `audit_logs`, permitiendo agrupar múltiples cambios de backend en una sola operación de usuario.

## 3. Esquema de la Tabla `audit_logs` (SSOT)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador único del evento de auditoría. |
| `correlation_id` | UUID | Agrupa múltiples eventos de backend en una sola acción de usuario. |
| `user_id` | String | Usuario responsable (del token JWT). |
| `client_ip` | String | IP de origen de la petición. Crucial para auditoría binacional. |
| `user_agent` | String | Agente de usuario del cliente (navegador, móvil, etc.). |
| `action` | Enum | `CREATE`, `UPDATE`, `DELETE`. |
| `table_name` | String | Nombre de la tabla/entidad afectada (ej. 'products'). |
| `record_id` | String | Clave primaria del registro afectado. |
| `old_value` | JSONB | Snapshot del estado del registro **antes** del cambio (solo para `UPDATE` y `DELETE`). |
| `new_value` | JSONB | Snapshot del estado del registro **después** del cambio (solo para `CREATE` y `UPDATE`). |
| `timestamp` | DateTime | Momento exacto del cambio, con zona horaria. |

## 4. Integración en la Aplicación FastAPI

Para activar la auditoría, se deben registrar el middleware y los listeners al iniciar la aplicación:

```python
# main.py
from fastapi import FastAPI
from common.middleware.audit import AuditMiddleware
from common.events.audit import register_audit_listeners

app = FastAPI()

# 1. Registrar listeners de SQLAlchemy
register_audit_listeners()

# 2. Añadir middleware de auditoría
app.add_middleware(AuditMiddleware)
```
## 5. Verificación de Integridad (Opcional - Fase 2)
Para una seguridad adicional, se puede añadir un campo `log_hash` a la tabla `audit_logs`. Este hash se calcularía a partir del contenido del `old_value`, `new_value` y el `timestamp`. Cualquier alteración posterior del registro invalidaría el hash, haciendo evidente la manipulación.