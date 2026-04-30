# InternoCore: Master Implementation History - 2026-04-30

## Architecture Change: HCM Microservice Extraction
Hoy se finalizó la transición del módulo de RRHH desde un componente interno del `auth-service` (legacy) hacia un microservicio autónomo e industrial: `hcm_service`.

### Key Decisions
1. **Decoupled Identity Persistence**: Los colaboradores físicos (identidades de piso) ahora residen en `hcm_db`, mientras que las credenciales digitales de usuario residen en `auth_db`. El vínculo se realiza mediante el `collaborator_id` inyectado en el JWT.
2. **Zero-Trust Edge Identity**: El JWT ahora transporta el `full_name` y el `internal_id` (badge) resueltos en el momento del login. Esto permite que los Kioscos y terminales de mano (Handhelds) muestren información del usuario sin realizar llamadas adicionales de "me/profile".
3. **Synchronized Hashing**: Se estableció el SSOT (Single Source of Truth) para la sal de RFID (`CORE_HR_RFID_SALT`) en el archivo `.env` global, asegurando que el despliegue local y AWS utilicen la misma lógica criptográfica.

### Technical Implementation
- **Handshake de Descubrimiento**: El `auth-service` actúa como orquestador. Si un colaborador no está vinculado a una empresa específica, el sistema consulta al `hcm_service` globalmente para descubrir a qué tenants pertenece el badge escaneado.
- **Middleware Compliance**: Se ajustaron los comandos de `select-company` y `collaborator-login` para cumplir con el esquema de respuesta estándar `{status, data, message}`, evitando errores de serialización.
- **Log Sanitization**: Se aplicó una política estricta de "No Emojis" en logs para prevenir fallos de codificación en el driver de AWS CloudWatch.

### Verification Result
- **RFID Flow**: Success (Luis Torres - Logistic MX).
- **PIN Flow**: Success with Discovery (Carlos Ramírez - Logistic US).
- **Code Graph**: 100% compliance.
