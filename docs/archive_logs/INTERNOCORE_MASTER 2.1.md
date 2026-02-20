📂 INTERNOCORE_MASTER.MD - The Single Source of Truth (SSOT)
Version: 2.2 (Refined)

Date: 2026-02-02

Status: Active / Architectural Enforcement

Documento Central: INTERNOCORE_MASTER.MD  Estado de sincronización: Backend (FastAPI) ↔ Frontend (Angular 19) Protocolo: Clean Architecture + Multitenancy Forzado.

1. Visión y ADN (Contexto Consolidado)
InternoCore es un MES modular diseñado para sectores de alta regulación.

Filosofía: "La configuración dicta el comportamiento".

Aislamiento: Multitenancy lógico estricto. Un usuario puede pertenecer a múltiples empresas, pero solo actúa en una a la vez.

Regla de Oro de Datos: El company_id es el ancla de toda la base de datos.

🏛️ 2. Arquitectura de Limpieza: El Eje "Common"
Para evitar la divergencia de código y asegurar que el Backend y el Frontend hablen el mismo idioma, se establece la Sincronización Obligatoria de Common.

A. Backend Common (backend/common/)
Este directorio es un espejo de la lógica de dominio de .NET y debe ser importable por todos los microservicios.

abstractions.py / base.py: Contiene BaseEntity (ID, Timestamps) y MultiTenantBase (obligatoriedad de company_id).

exceptions.py: Definición de DomainException, NotFoundException, etc., para asegurar que el ApiResponse sea consistente.

value_objects.py: Implementación de Money, Address, Quantity. No se usan tipos primitivos para datos de negocio complejos.

B. Frontend Common (frontend/src/app/common/ o shared/models/)
El frontend debe replicar la estructura de datos del backend para evitar errores de mapeo.

Interfaces Espejo: Cada entidad en Python debe tener su interface o type en Angular.

Prefix X-: Uso obligatorio de cabeceras X-Company-Id gestionadas por un interceptor global que lee del ContextService.

🛠️ 3. Protocolo de Creación de Archivos (Cleanliness)
Para mantener el proyecto libre de deuda técnica, cada nuevo módulo o entidad debe seguir este flujo de archivos:

Flujo Backend (Python)
Model: Heredar de BaseEntity y MultiTenantBase.

Schema (Pydantic): Crear el esquema de entrada y el esquema de salida (Response).

Repository/Command: Implementar la lógica de persistencia.

Controller: Exponer el endpoint usando el decorador de validación de tenant.

Flujo Frontend (Angular)
Model/Interface: Definir la estructura en models/.

Service: Crear el servicio inyectable que consuma el API.

Signals: Definir el estado local en el componente o store.

🔐 4. Flujo de Autenticación (Handshake Detallado)
POST /v1/auth/login: Credenciales -> Retorna selection_token + companies[].

POST /v1/auth/select-company: Recibe selection_token + company_id -> Retorna Access Token definitivo.

Importante: El Access Token contiene el company_id en el payload (JWT), pero el Frontend debe enviarlo también en el header X-Company-Id para facilitar el ruteo y logs en el backend.

✅ 5. Checklist de Estado y Próximos Pasos
Finalizado (Ready)
[x] SSOT Architecture: Definición de capas y responsabilidades.

[x] ApiResponse Standard: Formato {status, data, message, meta} implementado.

[x] Auth Handshake: Proceso de selección de empresa funcional.

🚩 Prioridad Inmediata (Fase AWS)
[ ] Configuración RDS (PostgreSQL): Creación de la base de datos gestionada en AWS.

[ ] Secrets Manager: Migración de .env locales a bóveda de secretos de AWS.

[ ] App Runner / ECS: Despliegue del primer microservicio (auth-service).

[ ] S3 + CloudFront: Host del frontend con SSL activo.

🔍 6. Guía de Trazabilidad y Refactor
Cada vez que el Agente AI cree un archivo, debe validar:

¿Hereda de Common? Si es una entidad de negocio, debe tener company_id.

¿El DTO coincide? El esquema Pydantic debe ser compatible con la Interface de Angular.

¿Verbose Logging? Toda creación debe ser notificada en el log: [FILE-CREATION] Created {path} mirroring {backend/frontend} structure.