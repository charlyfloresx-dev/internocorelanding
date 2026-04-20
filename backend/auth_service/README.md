# 🔐 Auth Service (Port 8000)

El **Auth Service** es el núcleo de identidad de **Interno Core**. Es el único servicio con autoridad para firmar tokens JWT y gestionar el ciclo de vida de la autenticación multi-tenant.

## 🛡️ Seguridad Zero-Trust
Interno Core sigue una arquitectura **Zero-Trust**. Bajo este esquema:
- **Firma Centralizada**: El Auth Service firma los tokens utilizando una clave compartida (`CORE_SECRET_KEY`) o par de llaves.
- **Validación Criptográfica**: Los demás microservicios no consultan la base de datos de Auth; validan el JWT en cada petición para confirmar la identidad.
- **Aislamiento de Contexto**: La identidad reside exclusivamente en el header `Authorization: Bearer <token>`.

## 🔄 Protocolo de Identidad (Handshake T1 / T2)
Para garantizar el aislamiento entre empresas, se utiliza un flujo de dos fases:

1. **Paso 1 (Login - T1):** El usuario envía credenciales a `/login`. Si son válidas, recibe un `selection_token` (T1) de solo lectura y la lista de empresas a las que tiene acceso.
2. **Paso 2 (Selección - T2):** El usuario envía el T1 al endpoint `/select-company`. El servicio valida la suscripción y emite el `access_token` (T2) definitivo con el contexto de la empresa seleccionada.

## 📖 Diccionario de Claims (JWT Payload)
El payload final del JWT está estandarizado para todo el ecosistema:
- `sub`: UUID único del usuario.
- `company_id`: UUID de la empresa activa.
- `group_id`: UUID del cluster corporativo (Holding).
- `roles`: Array de roles (ej. `["ADMIN", "OPERATOR"]`).
- `modules`: Módulos habilitados por suscripción (ej. `["wms", "mes"]`).
- `readonly`: Booleano que bloquea escrituras si hay impagos.
- `trace_id`: ID para trazabilidad distribuida (`X-Trace-Id`).

## 🏢 Jerarquía y Clusters
Mediante el `group_id`, el sistema soporta estructuras de holdings. Esto permite que empresas del mismo grupo (ej. "Corporativo Norte") compartan catálogos de Master Data y realicen transferencias de inventario inter-company validadas por cluster.
