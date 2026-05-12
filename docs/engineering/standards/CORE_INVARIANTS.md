# Core Invariants & Engineering Standards

Este documento define las reglas inmutables de ingeniería que garantizan la integridad, seguridad y trazabilidad del ecosistema **InternoCore**.

## 🏗️ 1. Estándares de Modelado (SQLAlchemy)

### 🛡️ AuditBase (Trazabilidad Total)
Todas las entidades de negocio deben heredar de `AuditBase`. Esto garantiza que cada registro tenga un rastro forense automático.
- `created_at` / `updated_at`: Timestamps automáticos.
- `created_by` / `updated_by`: UUID del usuario responsable.
- `transaction_id`: ID único para agrupar operaciones atómicas (Correlation ID).

### 🏢 MultiTenantBase (Muro de Hierro)
El aislamiento de datos es obligatorio. Ninguna consulta debe realizarse sin el filtro de `company_id`.
- El `BaseRepository` inyecta automáticamente el `company_id` extraído del JWT.
- Prohibido el uso de `IDOR` (Inyección manual de IDs de empresa desde el cliente).

## 💎 2. Objetos de Valor (Value Objects)
Para mantener la consistencia financiera, los siguientes campos deben seguir estructuras estrictas:
- **Money / Currency:** Uso mandatorio de decimales de precisión fija. Los precios se sellan al momento de la transacción (`Sealed Price`).
- **Address:** Estructura normalizada compatible con el proveedor GIS (ArcGIS Tijuana).

## 🔐 3. Seguridad Zero-Trust
- **Handshake T1/T2:** Protocolo de autenticación en dos pasos (Login -> Selección de Empresa).
- **JWT Lifespan:** 720 minutos (12 horas) para turnos industriales.
- **Auditoría de Acceso:** Todo intento de login y fallo de seguridad se registra en el `SecurityAuditLog`.

## 📡 4. Comunicaciones (API)
- **ApiResponse:** Formato estándar de respuesta `{ status, data, message, meta }`.
- **Error Handling:** Los errores 403 (Forbidden) y 402 (Payment Required) son reactivos y disparan bloqueos en el UI.

---
**Nota:** El incumplimiento de estos estándares disparará una violación en el `generate_code_graph.py` y bloqueará el despliegue a producción.
