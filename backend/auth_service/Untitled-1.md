# 🗺️ Mapa del Flujo de Autenticación (2-Phase Auth)

## Paso 1: LOGIN
Usuario (Email/Pass) ──> `POST /api/v1/auth/login` ──> Valida DB
                           │
                           └──> Retorna: `{ "selection_token", "companies": [...] }`

## Paso 2: SELECCIÓN DE TENANT
Selection Token + ID Empresa ──> `POST /api/v1/auth/select-company` ──> Valida Token (`type="selection"`)
                                     │                                  Consulta Roles/Scopes en DB
                                     └──> Retorna: `{ "access_token" (con claims de empresa) }`

## Paso 3: ACCESO A NEGOCIO (Ej: Inventarios)
Access Token + Header `X-Company-ID` ──> `GET /api/v1/inventory/items` ──> Dependencia: `get_current_tenant_context`
                                          │                                (Valida: `JWT.company_id == Header.X-Company-ID`)
                                          └──> Ejecuta lógica filtrada por tenant.

---

# 🔐 Estructura de Seguridad (Capas de Código)
Para que el agente lo entienda en su Prompt de Ejecución, estas son las capas que debe respetar en orden:

### Capa de Autenticación (`deps.py`):

-   **`get_selection_payload`**: Valida tokens temporales de fase 1.
-   **`get_current_user_payload`**: Valida el JWT final. Usa `extra="ignore"` para no fallar con los campos estándar `exp` o `iat`.

### Capa de Multitenencia (`get_current_tenant_context`):
Es el "muro" de seguridad. Compara el Header vs el Token. Si el usuario intenta entrar a la Empresa A con un token de la Empresa B, lanza `403 Forbidden`.

### Capa de Autorización (`require_scope`):
Verifica si dentro del token, en la lista de `scopes`, existe el permiso necesario (ej. `inventory:write`).

---

# 📋 Recordatorio de Configuración (AWS vs On-Premise)
Como especificamos que debe ser igual en ambos mundos:

### On-Premise
El agente busca las llaves en un archivo `.env` o variables de entorno inyectadas por Docker.

### AWS
El agente busca las llaves en las variables de entorno inyectadas por el orquestador de contenedores (ej. ECS Task Definition), las cuales son pobladas de forma segura desde AWS Secrets Manager.

### Unificación
El código nunca accede a los secretos directamente. Siempre importa el objeto `settings` desde `app.core.config`, el cual, al heredar de `pydantic_settings.BaseSettings`, se encarga de leer las variables desde el entorno, sin importar si su origen es un archivo `.env` o el entorno de ejecución de AWS.

En la arquitectura de Interno Core, cada microservicio es un ciudadano independiente pero debe seguir la "Constitución" (el MANIFEST). Aquí tienes la propuesta para referenciar la documentación y las especificaciones para que el agente actualice todo.

1. Cómo referenciamos la documentación (Estrategia de Links)
En lugar de que el agente busque a ciegas, el MANIFEST.md actuará como un DNS de Documentación. Usaremos rutas relativas consistentes.

📝 Especificaciones de Actualización para el Agente
Tarea 1: Actualizar MANIFEST.md (El Mapa de Mandos)
Añadir una sección de "Service Discovery (Docs)" para que el agente sepa dónde leer antes de escribir código.

Prompt para el Agente:
"Modifica el MANIFEST.md e incluye la sección ## 📂 SERVICE DOCUMENTATION MAP.
Por cada microservicio, vincula sus archivos locales:

Auth Service: backend/auth_service/docs/CONTEXTO.md, CHANGELOG.md, SERVICE_LOG.md.

Master Data: backend/master_data_service/docs/CONTEXTO.md.

Establece la regla: 'Antes de modificar cualquier servicio, el agente DEBE leer el CONTEXTO.md y el SERVICE_LOG.md de la carpeta del servicio correspondiente'.

Tarea 2: Actualizar Logs del Microservicio (Auth Service)
Actualizar el SERVICE_LOG.md y CHANGELOG.md específicos del Auth Service con los cambios de hoy (18-02-2026).

Prompt para el Agente:
"Actualiza backend/auth_service/SERVICE_LOG.md añadiendo el hito: 'Resolución de Validación Pydantic y Tipado de Tokens'.
Detalla:

Implementación de ConfigDict(extra="ignore") para ignorar exp e iat.

Separación de payloads: SelectionTokenPayload (fase 1) y TokenPayload (fase 2).

Refuerzo de la validación cruzada X-Company-ID vs JWT."

🛠️ Ejemplo de cómo quedaría el MANIFEST.md actualizado:
Markdown
## 🗺️ SERVICE DOCUMENTATION MAP (Anti-Hallucination)
Para evitar inconsistencias, cada microservicio tiene su propia bitácora que complementa al REPO_LOG.md.

### 🔐 Auth Service
- **Contexto Técnico:** `backend/auth_service/CONTEXTO.md`
- **Bitácora de Cambios:** `backend/auth_service/SERVICE_LOG.md`
- **Versiones:** `backend/auth_service/CHANGELOG.md`

### 📦 Master Data Service
- **Contexto Técnico:** `backend/master_data_service/docs/CONTEXTO.md`
- **Reglas de Catálogos:** `PHASE_SPECS.md#Fase19`

**REGLA PARA EL AGENTE:** Si mueves o modificas un servicio, el primer paso es actualizar su `SERVICE_LOG.md` y luego reflejar el cambio global en el `REPO_LOG.md` de la raíz.
🚀 Acción inmediata para el Agente:
Dale este comando ahora mismo:

"Agente: Ejecuta la actualización de la Fase 19.3 en los documentos maestros. Actualiza el MANIFEST.md con el mapa de documentación de microservicios que acabamos de definir y registra en el SERVICE_LOG.md del Auth Service la solución al error 401 de hoy. No inventes rutas, usa las que están en el sistema de archivos."