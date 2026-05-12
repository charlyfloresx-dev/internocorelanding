# Forensic Ledger Policy - El Ciclo de Vida de la Verdad

Este documento define el protocolo técnico para la captura, almacenamiento y protección de la evidencia digital en **InternoCore**. El Ledger Forense es el componente inmutable que garantiza la confianza en entornos industriales y SaaS.

## 🏛️ 1. El Snapshot de Estado (Before/After)
Cada mutación de datos (CREATE, UPDATE, DELETE) en una entidad protegida por `AuditBase` debe generar un registro en el `ForensicAuditLog`.

- **Payload de Datos:** Se almacena el snapshot completo del objeto en formato JSONB.
- **Diferencial (Diff):** Para operaciones de actualización, se recomienda registrar el diferencial para facilitar auditorías rápidas.
- **Inmutabilidad:** Los registros de auditoría no permiten actualizaciones ni eliminados (Append-Only).

## 🆔 2. Trazabilidad del Colaborador
Ninguna acción es anónima. Cada registro en el ledger debe estar vinculado a:
- **`user_id`**: El UUID del usuario autenticado.
- **`company_id`**: El tenant donde se originó la acción.
- **`transaction_id`**: Un ID único (Correlation ID) que vincula múltiples cambios en una sola operación lógica (ej. una venta que afecta inventario y finanzas).
- **Metadata de Red**: Dirección IP y User-Agent del cliente.

## 🏢 3. Aislamiento Multi-tenant
La integridad del ledger se garantiza mediante:
- **Aislamiento Lógico:** Las consultas de auditoría están filtradas por el `company_id` del JWT activo.
- **Segregación de Vistas:** Los logs de la Empresa A son invisibles para la Empresa B, incluso a nivel de base de datos si se escala a esquemas separados.

## 📜 4. Protocolo para Microservicios
Cualquier servicio nuevo debe implementar el `AuditMiddleware` o heredar de `AuditRepository` para:
1. Capturar el contexto de la transacción desde los headers.
2. Serializar el estado previo de la entidad.
3. Persistir el cambio y el snapshot en la tabla de auditoría centralizada.

---
**Juramento de Integridad:** "Si no está en el Ledger, no sucedió."
