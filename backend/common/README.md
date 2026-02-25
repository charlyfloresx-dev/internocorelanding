# 🧬 Manifiesto del ADN (InternoCore Common)

Este módulo contiene la lógica fundamental y los pilares arquitectónicos que deben ser compartidos por todos los microservicios de la plataforma.

## 🏛️ Pilares Obligatorios (Mixins)

### 1. BaseEntity (Identity)
- **Mirror:** `Interno.Domain.BaseEntity`.
- **Propósito:** Garantiza que toda entidad tenga una identidad única basada en UUID (String 36).
- **Uso:** Fundamental para la consistencia en entornos distribuidos y sincronización con S3/Cloud.

### 2. AuditBase (History)
- **Mirror:** `Interno.Domain.AuditBase`.
- **Propósito:** Proporciona campos automáticos de auditoría: `created_at`, `updated_at`, `created_by` y `updated_by`.
- **Regla:** Todo registro de negocio debe ser auditable.

### 3. MultiTenantBase (Isolation)
- **Mirror:** `Interno.Domain.MultiTenantBase`.
- **Propósito:** Fuerza el aislamiento de datos mediante la columna `company_id`.
- **Seguridad:** El `company_id` es **MANDATORIO** (`nullable=False`) y se valida en cada transacción mediante el middleware de seguridad.

## 🛡️ Seguridad Transversal (Subscription Guard)

Todos los microservicios deben validar el acceso basado en la suscripción del tenant.

### Uso en FastApi
Para proteger un router o endpoint, utiliza la dependencia `SubscriptionGuard`:

```python
from common.security.subscription_guard import SubscriptionGuard

# Protege todo el router para el módulo 'inventory_core'
router = APIRouter(dependencies=[Depends(SubscriptionGuard("inventory_core"))])
```

**Comportamiento:**
1. **Entitlement:** Valida que el `module_code` esté en el claim `modules` del JWT.
2. **Read-Only:** Si el claim `readonly` es `true`, bloquea cualquier método de escritura (POST, PUT, DELETE) devolviendo un `403 Forbidden`.
3. **Excepción:** El `auth_service` está exento de la validación de módulos para permitir la gestión de la cuenta.

### Contrato de TokenPayload (SSOT)
El guardia y el sistema de identidad asumen este esquema obligatorio:
- `role`: (`OWNER`, `ADMIN`, `OPERATOR`). Fuente de verdad para permisos estructurales.
- `modules`: Lista de códigos habilitados (ej: `['inventory_core']`).
- `readonly`: Booleano que fuerza el modo lectura (bloquea escrituras).
- `accessible_warehouses`: Array de UUIDs para RBAC por sucursal.
- `correlation_id`: ID de rastreo forense (transaction_id).

## 🚀 Reglas de Oro
- **Paridad Híbrida (On-Premise / AWS):** Innegociable. El código debe abstraer la infraestructura (ej. S3 vs Local) mediante variables de entorno y patrones de repositorio. Nadie debe escribir código dependiente de un proveedor específico fuera de la capa de infraestructura.
- **No Deletion:** El código legacy se archiva, no se borra.
- **Inmutabilidad:** Las bases del ADN son espejos de .NET y no deben alterarse sin una revisión de arquitectura global.
