# Protocolo de Autenticación Handshake T1/T2

Este documento detalla el flujo de autenticación **Zero-Trust** de InternoCore, diseñado para garantizar el aislamiento multi-tenant y la delegación segura de sesiones en dispositivos industriales.

## 🔄 Flujo de Autenticación

### Fase 1: Identificación (T1)
- **Endpoint:** `POST /auth/login`
- **Payload:** `{ email, password }`
- **Resultado:** Retorna un `selection_token` (JWT de vida corta) y un listado de las empresas (`companies`) a las que el usuario tiene acceso.
- **Restricción:** El `selection_token` no permite realizar operaciones de negocio; solo da acceso al endpoint de selección.

### Fase 2: Selección de Tenant (T2)
- **Endpoint:** `POST /auth/select-company`
- **Headers:** `X-Selection-Token`
- **Payload:** `{ company_id }`
- **Resultado:** Retorna el **JWT Final de Operación**.
- **Contenido del JWT:**
    - `user_id`: Identidad global.
    - `company_id`: El tenant activo para esta sesión.
    - `roles`: Permisos específicos del usuario en esa empresa.
    - `scopes`: Módulos autorizados según la suscripción.

## 🔐 Rotación y Seguridad
- **Access Token:** Validez de 12 horas (720 min) para flujos industriales.
- **Refresh Token:** Almacenado en la base de datos de identidad con protección contra Replay Attacks.
- **Aislamiento IDOR:** El sistema ignora cualquier `company_id` enviado por el cliente en las cabeceras de peticiones de negocio; siempre utiliza el `company_id` sellado dentro del JWT firmado.

## 📱 Delegación QR (Zero-Trust Mobile)
Para dispositivos móviles sin teclado (Handhelds):
1. El usuario se autentica en una terminal de confianza (Web).
2. Genera un QR de delegación vía `/auth/delegate-selection`.
3. El móvil escanea el QR, recibe el `selection_token` y el `company_id`, y completa el Handshake T2 automáticamente.
