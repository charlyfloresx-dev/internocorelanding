# Historial de Implementación - 14 de Abril 2026

## Objetivos Alcanzados
1. **Industrialización de Identidad**: Transición exitosa de `internal_id` de `Integer` a `String(50)` para soportar formatos de nómina binacionales.
2. **Handshake Multi-Tenant**: Refactorización del login de colaboradores para permitir descubrimiento global de identidad (RFID/PIN) con redirección dinámica a la empresa correcta.
3. **Estandarización en la Nube**: Estandarización de 11 microservicios para usar prefijos `CORE_` compatibles con AWS Secrets Manager y Parameter Store.
4. **Resiliencia de Hardware**: Implementación de limpieza de entradas (`.strip()`) para manejar caracteres invisibles devueltos por escáneres físicos.
5. **Cross-Tenant Identity Bridge**: Implementación de "identity jumping" en HR Service usando credenciales físicas compartidas (RFID/Código de barras) entre diferentes registros de tenant.
6. **Alineación de Scopes Frontend**: Mapeo de permisos industriales a scopes administrativos (`inv:movements:manage`) para garantizar el renderizado correcto del menú lateral.
7. **Resiliencia Zero-Trust**: Bypass del endpoint `/me` para colaboradores industriales, resolviendo perfiles directamente desde los claims del JWT.

## Decisiones Arquitectónicas (SSOT)
- **Middleware Unificado**: Se decidió eliminar `TenantSecurityMiddleware` local y absorber su lógica en `InternoCoreGlobalMiddleware` (librería `common`). Esto garantiza que las rutas públicas se gestionen en un solo lugar y evita colisiones de headers.
- **Validación Dinámica**: Los patrones de validación de ID interno se movieron de Pydantic (estático) a Service Layer (dinámico) consultando `HrTenantConfig` para permitir cambios de reglas de negocio sin desplegar código.
- **Hachís de RFID**: Uso de `RFID_STATIC_SALT` inyectado por entorno para asegurar que las tarjetas físicas tengan lookups O(1) pero sean seguras contra Rainbow Tables.
- **Identidad Virtual de Planta**: Se estableció el patrón de "Usuario Virtual" para operadores industrializados, donde el Auth Service delega la verificación al HR Service en tiempo real, evitando redundancia de datos personales en la base de datos de autenticación.

## Bloqueadores Resueltos
- **Error 400 (Lockdown)**: Se resolvió un error en la whitelist del middleware global que exigía `X-Company-ID` en rutas de login por una barra diagonal mal colocada.
- **Error 401 (Mismatched Hash)**: Se identificó y resolvió una inconsistencia entre el salt de desarrollo y el de Docker, unificando todo bajo el estándar `CORE_`.
- **Alphanumeric ID**: Se corrigió el error `Invalid input for type integer` migrando todas las capas (DB, Model, Schema) a String.
- **Error 500 en Perfil**: Se resolvió la caída del Dashboard al intentar cargar perfiles de oficina para usuarios industriales mediante la inyección de metadatos de identidad directo en el SecurityContext.
- **Menú Vacío (Sidebar)**: Corregido mediante el mapeo dinámico de permisos industriales a scopes técnicos compatibles con Angular.

## Variables de Entorno Introducidas
- `CORE_HR_RFID_SALT`: Salt maestro para dispositivos físicos.
- `CORE_INTERNAL_API_KEY`: Secreto compartido para comunicación inter-servicios blindada.
- `CORE_DATABASE_URL`: Estandarización de conexión en todos los contenedores.
