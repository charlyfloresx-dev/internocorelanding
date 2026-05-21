# InternoCore: Protocolo de Sincronización de Documentación (Sync-Docs)

Este flujo de trabajo garantiza que la "fuente de verdad" documental esté siempre alineada con el código desplegado, evitando la deuda técnica y manteniendo el control arquitectónico (FinOps, Seguridad y Estructura).

## Disparadores (Triggers)
Ejecutar este workflow cuando:
1. Se despliega un nuevo microservicio en AWS (ECS o App Runner).
2. Se resuelve un bug crítico que involucra cambios en configuración (`env`, dependencias, DB).
3. Se finaliza una Fase Arquitectónica importante.

## Tareas

### 1. Auditoría del Gráfico de Código (Code Graph) & SaaS Integrity
Ejecutar el script de auditoría automatizada para validar _Invariants_ (FinOps, CORS, Multi-tenant, y Subscription Guard):
// turbo
```bash
python backend/scripts/generate_code_graph.py
```
> **Validación:** Si el script reporta `SUBSCRIPTION_GUARD_VIOLATION` o cualquier `CRITICAL`, detener el workflow. El sistema no es seguro para producción con fugas en el paywall o violaciones de arquitectura.

### 1.5. Verificación de Endpoints Internos HMAC (Inter-Service Security)
Confirmar que los endpoints inter-servicio estén protegidos contra acceso sin firma:
// turbo
```powershell
# tickets_service — debe retornar 403
Invoke-WebRequest -Uri "http://localhost:8008/api/v1/tickets/internal" -Method POST -ContentType "application/json" -Body '{}' | Select-Object StatusCode
# Esperado: 403 "Firma de servicio requerida"

# subscription_service — debe retornar 403
Invoke-WebRequest -Uri "http://localhost:8002/internal/status/00000000-0000-0000-0000-000000000001" | Select-Object StatusCode
# Esperado: 403 "Firma de servicio requerida"
```
> **Validación:** Cualquier endpoint `/internal/*` que retorne 200 sin `X-Service-Signature` es una brecha de seguridad. Detener y corregir antes de documentar.

### 2. Prueba de Fuego Sensorial (Stripe Webhook)
Validar que el bloqueo reactivo funcione en tiempo real:
// turbo
```bash
& "C:\Users\flore\Downloads\stripe_1.37.2_windows_x86_64\stripe.exe" trigger invoice.payment_failed
```
> **Validación:** Confirmar visualmente el banner de "Pago Pendiente" o el error 402 en consola de red. No documentar si el webhook falla o el bypass de desarrollo está roto.

### 3. Actualizar Documentación de Infraestructura & Orquestación
Revisar la carpeta `infrastructure/` y verificar que el `README.md` maestro esté alineado con los puertos y servicios actuales.
Puntos críticos a verificar:
- `infrastructure/docker/docker-compose.dev.yml`: ¿Los healthchecks y nuevos servicios (whatsapp-gateway) están configurados?
- `infrastructure/docker/migrate_all.ps1`: ¿Todos los servicios con DB propia tienen su migración incluida? (auth, subscription, master_data, hcm, inventory, tickets, notification)
- `CLAUDE.md` tabla de servicios: ¿Coincide con el `docker ps` real?

### 3.5. Validación del Ecosistema Local (Ping Maestro)
Asegurar que el orquestador esté levantado y enrutando correctamente antes de documentar:
// turbo
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_ecosystem.ps1
```
> **Validación:** Confirmar que todos los servicios reporten `[ OK ]` o estatus HTTP esperados, garantizando la salud del API Gateway.

### 3.6. Verificación del WhatsApp Gateway (si la fase lo afectó)
Solo ejecutar si hubo cambios en `backend/whatsapp_gateway/` o `notification_service`:
// turbo
```powershell
# Verificar que el contenedor esté levantado
docker ps --filter "name=interno-whatsapp-gateway-dev" --format "table {{.Names}}\t{{.Status}}"

# Verificar que el health del gateway responde (sin Auth → debe rechazar)
Invoke-WebRequest -Uri "http://localhost:3011/api/v1/whatsapp/session/test/status" -ErrorAction SilentlyContinue | Select-Object StatusCode
# Esperado: 401 (correcto — el Gateway rechaza sin Bearer token)

# Verificar proxy seguro vía Notification Service (con JWT admin válido)
# GET http://localhost:8009/api/v1/whatsapp/session/status
# Header: Authorization: Bearer <admin_jwt>
# Esperado: { "status": "success", "data": { "status": "NOT_INITIALIZED" } }
```
> **Validación multitenancy (Muro de Hierro ADR-02):** El `company_id` debe venir SIEMPRE del JWT — nunca del cuerpo ni path del cliente. Verificar en logs de gateway que la sesión consultada corresponde al tenant del token.

### 4. Actualizar Bitácoras de Ingeniería (REPO_LOG y SERVICE_LOG)
Escribir un resumen breve en el `REPO_LOG.md` raíz con los detalles de la fase actual (Objetivos, Decisiones Arquitectónicas y Workarounds).

**IMPORTANTE:** Replicar un resumen técnico adaptado en el respectivo `SERVICE_LOG.md` de cada microservicio afectado. Si hubo cambios en puertos, variables de entorno o servicios Docker, actualizar también `CLAUDE.md` (tabla sección 2).

Formato de entrada para `REPO_LOG.md`:
```
## Phase XXX — Título Corto (YYYY-MM-DD)
**Objetivos:** ...
**Decisiones Arquitectónicas:** ...
**Workarounds / Deuda Técnica:** ...
**Archivos clave:** ...
```

### 4.5. Consolidados Diarios y Planes de Implementación
Para no contaminar la raíz documental, dividir y clasificar la jornada obligatoriamente respetando esta nomenclatura estricta:
- **Tareas del Día**: Crear o actualizar `docs/historial/tasks/consolidated_tasksYYYYMMDD.md` capturando backlog superado y pendientes.
- **Planes de Implementación**: Crear `docs/historial/implementation/master_implementation_historyYYYYMMDD.md` registrando la arquitectura planeada/ejecutada del día.

### 5. Confirmación Segura (Git Versioning)
Finalmente, empaquetar de forma segura toda la arquitectura confirmando el commit.
// turbo
```bash
git add .
git commit -m "docs(architecture): sync-docs Phase XXX — <descripcion-corta>"
```
> **Convención de mensaje:** Formato obligatorio `docs(architecture): sync-docs Phase XXX — <descripcion>`. Usar `feat(...)`, `fix(...)`, `security(...)` en commits de código; solo `docs(architecture)` en commits de sincronización pura.

## Criterios de Éxito
- `generate_code_graph.py` reporta 0 CRITICALs (exit code 0).
- Todos los endpoints `/internal/*` retornan 403 sin `X-Service-Signature`.
- Los Markdowns en `/docs` reflejan comandos copiables y verídicos sobre la última iteración.
- `REPO_LOG.md` cuenta la historia del estado actual de forma secuencial.
- `CLAUDE.md` tabla de servicios coincide con `docker ps` real.
