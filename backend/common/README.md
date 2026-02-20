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

## 🚀 Reglas de Oro
- **Paridad Híbrida (On-Premise / AWS):** Innegociable. El código debe abstraer la infraestructura (ej. S3 vs Local) mediante variables de entorno y patrones de repositorio. Nadie debe escribir código dependiente de un proveedor específico fuera de la capa de infraestructura.
- **No Deletion:** El código legacy se archiva, no se borra.
- **Inmutabilidad:** Las bases del ADN son espejos de .NET y no deben alterarse sin una revisión de arquitectura global.
