# 📂 InternoCore

InternoCore es una plataforma modular de ejecución de manufactura (MES) diseñada para despliegues híbridos (On-Premise / Cloud). Su objetivo es unificar la gestión de inventario, producción, calidad y operaciones en un único ecosistema.

Este repositorio está siendo activamente refactorizado para migrar de una arquitectura monolítica .NET a una moderna basada en microservicios con Python (FastAPI) y un frontend en Flutter.

## 🏛️ Fuente Única de Verdad (SSOT)

Toda la arquitectura, principios, y hoja de ruta del proyecto están documentados en el siguiente archivo. Es de lectura obligatoria para entender el proyecto.

➡️ **[INTERNOCORE_MASTER.md](./INTERNOCORE_MASTER.md)**

---

## 🚀 Cómo Empezar (Entorno Local)

### Prerrequisitos
- Docker y Docker Compose
- Un cliente de línea de comandos (bash, zsh, etc.)
- Haber copiado `.env.example` a `.env` y configurado las variables.
- **Variables de Entorno Cruciales para Auth-Service:**
    - `SECRET_KEY`: Una cadena secreta larga y aleatoria para firmar JWTs. **CAMBIAR EN PRODUCCIÓN.**
    - `ACCESS_TOKEN_EXPIRE_MINUTES`: Duración en minutos del JWT de acceso final (ej: `60`).
    - `SELECTION_TOKEN_EXPIRE_MINUTES`: Duración en minutos del token de selección temporal (ej: `5`).
    - `ALGORITHM`: Algoritmo de cifrado para JWT (ej: `HS256`).

### 1. Validar Entorno
Antes de empezar, ejecuta el script de validación para asegurar que tu entorno cumple los requisitos.

```bash
./scripts/validate_local.sh
```

### 2. Iniciar la Base de Datos y Servicios Base
Este comando levanta la base de datos (PostgreSQL por defecto) y MinIO (almacenamiento S3 local).

```bash
./scripts/init_db.sh
```

### 3. Levantar los Servicios de Aplicación (Auth + Warehouse)
Este comando levanta los contenedores de los servicios de `auth-service` y `warehouse-service` en modo de desarrollo (con hot-reloading).

```bash
docker-compose -f docker/docker-compose.dev.yml up -d auth-service # warehouse-service (cuando esté listo)
```

### 4. Aplicar Migraciones de Base de Datos
Aplica las migraciones de la base de datos para el servicio de autenticación. Esto creará las tablas para Roles, Permisos, y las tablas de asociación.

```bash
./scripts/migrate.sh auth-service
```

### 5. Cargar Datos de Prueba (Opcional)
Este comando puebla la base de datos con datos iniciales, como una compañía, un usuario administrador, y roles/permisos básicos. **Es crucial ejecutarlo después de las migraciones para inicializar roles y permisos.**

```bash
python scripts/seed_data.py
```

### 🔐 Flujo de Autenticación de Dos Pasos y Multi-Tenancy

El Auth-Service ahora implementa un flujo de autenticación en dos fases para soportar multi-tenancy:

1.  **Login (Pre-Auth): `POST /api/v1/auth/login`**
    *   Envía `email` y `password`.
    *   Recibe un `selection_token` (JWT de corta duración sin privilegios) y una lista de las `companies` a las que el usuario pertenece. Cada `company` en el array incluye `isNew` (para el usuario en esa empresa), `logo` y `name`.

2.  **Selección de Empresa (Contextualización): `POST /api/v1/auth/select-company`**
    *   Envía el `company_id` deseado y el `selection_token` en el header `X-Selection-Token`.
    *   Recibe el `access_token` final (JWT con `user_id`, `company_id`, `roles`, `permissions` y `exp`).

### 🛡️ Uso del `access_token` y `X-Company-ID` en Solicitudes Protegidas

Una vez obtenido el `access_token` final, debes usarlo en todas las solicitudes protegidas:

*   **Header `Authorization`**: Incluye el `access_token` con el prefijo `Bearer` (ej: `Authorization: Bearer <your_access_token>`).
*   **Header `X-Company-ID`**: **Debes enviar el `company_id` de la empresa seleccionada** en este header para cada solicitud. El middleware de seguridad validará que este `company_id` coincida con el `company_id` dentro de tu `access_token`. Esto asegura que todas las operaciones se realicen en el contexto de la empresa correcta.

---

## ✅ Checklist de Implementación y Tareas Pendientes de Alta Prioridad

Este es un resumen del progreso y los siguientes pasos críticos para el flujo de usuario-empresa.

### Implementado y Verificado:

*   **Contrato de Autenticación y Tenancy (#001)**:
    *   Propiedad de Identidad (Auth-Service dueño de Users, N:N con empresas).
    *   Esquema de Respuesta Único (`StandardResponse` en todos los endpoints).
    *   Flujo Stateless en Dos Tiempos (T1: Login Pre-Auth; T2: Selección de Empresa).
    *   Cálculo y envío del flag `isNew` en `selection_token` (Login Pre-Auth).
    *   Inclusión del campo `logo` en la información de la empresa en el Login Pre-Auth.
    *   Uso de `transaction_id` (mapeado de `trace_id`) en `meta` de `StandardResponse`.
    *   Logging de movimientos recientes en endpoints de autenticación.
*   **CRUD Básico para Compañías**:
    *   Modelos, Schemas y Endpoints (`POST`, `GET`, `PUT`, `DELETE`).
*   **Relación N:N para Usuarios y Empresas**:
    *   Modelos `Role`, `Permission`, `UserCompanyRole`.
    *   Schemas y relaciones actualizadas en `User` y `Company`.
*   **Middleware de Seguridad**:
    *   Función de dependencia (`get_current_user_payload`) que valida JWT y `X-Company-ID`.

### Tareas Pendientes de Alta Prioridad:

1.  **Manejo Detallado de Roles y Permisos (Sembrado de Datos)**:
    *   Implementar un script de `seed_data.py` más robusto que cree roles (`Admin`, `Member`, etc.) y permisos (`read:users`, `write:products`) por defecto, y asigne roles a usuarios en empresas específicas. Esto es crucial para probar el flujo completo.
    *   Considerar la creación de endpoints de administración para gestionar Roles y Permisos.
2.  **Flujo 'Usuario sin empresa'**:
    *   Definir y validar el comportamiento exacto cuando un usuario se registra sin un `company_id` o no pertenece a ninguna empresa. ¿Cómo se le invita a crear una empresa o unirse a una existente?
    *   Crear endpoints para:
        *   Unir a una empresa existente (solicitud/aceptación).
        *   Crear una nueva empresa y auto-asignarse como `Admin`.
3.  **Flujo 'Usuario con N empresas'**:
    *   Asegurar que la lógica de `my-companies` y `select-company` maneje correctamente escenarios con múltiples empresas y roles diferentes para un mismo usuario.
    *   Implementar mecanismos para que el usuario pueda gestionar sus empresas (ej. abandonar una empresa, cambiar su rol si tiene permisos).
4.  **Refinamiento del flag `isNew`**:
    *   Definir con mayor precisión qué constituye "registros de actividad o perfil completo" para el flag `isNew`. Si se requiere persistencia por empresa, crear la tabla `UserProfileCompanyContext` recomendada en `DOC_AUDITORIA_ESTADO.md`.
    *   Integrar esta lógica en el cálculo de `isNew`.
5.  **Pruebas End-to-End**:
    *   Crear un conjunto exhaustivo de pruebas que cubra los flujos de autenticación de dos pasos, creación de usuarios/empresas, asignación de roles y la validación del middleware de seguridad.

---

¡Listo! Los servicios deberían estar corriendo y accesibles en los puertos definidos en `docker/docker-compose.dev.yml`.
