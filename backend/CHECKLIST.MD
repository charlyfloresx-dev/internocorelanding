# 🚀 Checklist de Desarrollo - InternoCore v2.1

## 1. Fase: Infraestructura y Modelos (Punto Actual 📍)
- [x] 1.1 Configurar `common/models.py` implementando `BaseEntity`, `AuditBase` y `MultiTenantBase` (Mirror .NET).
- [ ] 1.2 Crear Script de Seed (`seed.py`) con usuario `charly@internocore.app` y enums `UserStatus`/`CompanyStatus`.
- [ ] 1.3 Levantar Docker y ejecutar migraciones (Verificar `company_id` obligatorio en tablas de negocio).

## 2. Fase: Middleware y Estructura Global
- [x] 2.1 Implementar `InternoCoreGlobalMiddleware` en `main.py` y `common/middleware.py`.
- [x] 2.2 Validar formato JSON `data/meta` y `X-Transaction-ID` en un endpoint de prueba.

## 3. Fase: Lógica de Autenticación Dual
- [x] 3.1 Endpoint `POST /auth/login` (Retorna `CompanyAccessDto` y Selection Token).
- [x] 3.2 Endpoint `GET /auth/my-companies` (Lista de empresas vinculadas con `isNew` y `logo`).
- [x] 3.3 Endpoint `POST /auth/select-company` (Access Token Contextual - 8 hrs).

## 4. Fase: Integración con Frontend (IA Studio Alignment)
- [ ] 4.1 Alinear el Interceptor de Angular/Typescript con el JSON de la API.
- [ ] 4.2 Probar flujo completo: Login -> Selección -> Dashboard.

## 5. Fase: Despliegue y Onboarding (AWS Prep)
- [ ] 5.1 Preparar script de despliegue único para AWS (Secrets Manager).
- [ ] 5.2 Implementar flujo de aprobación de empresas (Onboarding State).

---

## 📝 Registro de Auditoría de Arquitectura (Log)

### [AUDIT-2026-01-24] - Alineación Técnica Auth-Service
- **Objetivo:** Verificar cumplimiento con Clean Architecture y soporte Multi-tenant estricto.
- **Hallazgos:**
    - **Common Lib:** Se requiere estricta paridad con `Interno.Common` (.NET). `MultiTenantBase` debe ser la clase base para todas las entidades de negocio.
    - **Identidad:** El DTO de respuesta de login debe mapear correctamente a `CompanyAccessDto` para el frontend.
    - **Seguridad:** Confirmado uso de Bcrypt 4.0.1. Secretos listos para migración a AWS Secrets Manager.
    - **Onboarding:** Se detectó necesidad de un estado intermedio "PendingApproval" en `CompanyStatus` para el flujo de creación de empresas.

### [AUDIT-2026-01-24] - Validación Clean Architecture & Multi-tenancy
- **Estado:** ✅ Conforme (Common Layer).
- **Clean Architecture:** La abstracción de `BaseEntity` y `AuditBase` en `common` permite desacoplar la lógica de infraestructura de los modelos de dominio específicos de cada microservicio.
- **Multi-tenancy:** El mixin `MultiTenantBase` impone `company_id` obligatorio y con índice, garantizando el aislamiento de datos a nivel de esquema.
- **Conectividad:** Se reportó `ERR_CONNECTION_REFUSED`. Se recomienda verificar binding `0.0.0.0` en Dockerfile/Compose.
- **Modelado:** Se agregaron `UserStatus` y `CompanyStatus` (con estado 'Pending') para soportar flujos de aprobación asíncronos.

## ✅ Directivas InternoCore Implementadas

Las siguientes directivas han sido completamente implementadas y verificadas en el Auth-Service:

### DIRECTIVA INTERNO-CORE #001: CONTRATO DE AUTENTICACIÓN Y TENANCY
- [x] **Propiedad de Identidad**: Auth-Service es dueño de `Users`, relación N:N con `Companies` a través de `UserCompanyRole`.
- [x] **Esquema de Respuesta Único**: Todas las respuestas siguen el formato `{ "status": "success/error", "data": {...}, "message": "...", "meta": {...} }` utilizando `StandardResponse`.
- [x] **Flujo Stateless en Dos Tiempos**:
    - [x] **T1 (Auth)**: `POST /api/v1/auth/login` emite un `selection_token` (JWT temporal) con `user_id` y array de `tenants` (empresas asociadas con `isNew`, `logo`, `name`).
    - [x] **T2 (Context)**: `POST /api/v1/auth/select-company` devuelve el JWT definitivo con `company_id` y `roles` incrustados.
- [x] **Flag `isNew`**: Calculado dinámicamente en `POST /api/v1/auth/login` y agregado al `SelectionTokenResponse`.
- [x] **Logging**: Se agregó logging para movimientos recientes, incluyendo el flag `isNew` y detalles relevantes.
- [x] **Middleware Global**: `InternoCoreGlobalMiddleware` implementado en `backend/common/middleware.py` para sincronizar `transaction_id` (`X-Transaction-ID`) y envolver respuestas/excepciones en `StandardResponse`.

### DIRECTIVA #002: SINCRONIZACIÓN DE DISCOVERY-LOGIN
- [x] **Backend**: El endpoint `/login` solo emite el `discovery_token` (nuestro `selection_token`), no permisos finales.
- [x] **Payload de Discovery**: El objeto `tenants` (`companies`) dentro de `data` es el resultado de un JOIN entre `users`, `user_tenants` (nuestro `UserCompanyRole`) y `companies`.
- [x] **Frontend**: La lógica backend soporta que el frontend no acceda a rutas protegidas sin el JWT final (emitido por `/select-company`).
