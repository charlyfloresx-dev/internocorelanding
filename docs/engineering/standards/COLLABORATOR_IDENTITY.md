# Esquema de Identidad y Permisos: Evolución del Colaborador

Este documento detalla el cambio estratégico de paradigma en la gestión de talento humano e identidad dentro de InternoCore, pasando de un modelo de "operadores" a uno de **"Colaboradores Industriales"**.

## 🔄 1. Transición Semántica y Técnica
El rol anteriormente conocido como `production_operator` ha sido unificado bajo la entidad global de **Colaborador**.
- **Impacto en BD:** La tabla `collaborators` en el `hr_service` es ahora el SSOT (Single Source of Truth) para la identidad física.
- **Vínculo de Identidad:** Se utiliza el `collaborator_id` para vincular transacciones en el `inventory_service` cuando la acción es realizada físicamente en piso, incluso si el usuario no tiene una cuenta de correo corporativa (uso de PIN/RFID).

## 🔐 2. Matriz de Permisos (RBAC)
Los colaboradores operan bajo una jerarquía de permisos basada en **Entitlements**:
- **`inventory_reader`**: Consulta de saldos y ubicación de SKUs.
- **`inventory_operator`**: Capacidad para ejecutar movimientos de Kardex (Entradas/Salidas).
- **`pos_operator`**: Acceso al flujo de Punto de Venta y Handshake T2.

## 📱 3. Identidad en Dispositivos Industriales (QR/Zebra)
El protocolo **Handshake T2** es el mecanismo que eleva la identidad del colaborador al dispositivo móvil:
1. El colaborador escanea su código QR personal (firmado por el `hr_service`).
2. El sistema valida el `collaborator_id` contra el `user_id` vinculado (si existe) o genera una sesión volátil de operador protegida por el `transaction_id`.
3. Todas las acciones realizadas en la Zebra quedan selladas con la identidad del colaborador en el Ledger Forense.

---
**Gobernanza:** "En InternoCore, cada colaborador es un guardián de la integridad del inventario."
