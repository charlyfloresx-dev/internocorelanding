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
> **Validación:** Si el script reporta `SUBSCRIPTION_GUARD_VIOLATION`, detener el workflow. El sistema no es seguro para producción si hay fugas en el paywall industrial.

### 2. Prueba de Fuego Sensorial (Stripe Webhook)
Validar que el bloqueo reactivo funcione en tiempo real:
// turbo
```bash
& "C:\Users\flore\Downloads\stripe_1.37.2_windows_x86_64\stripe.exe" trigger invoice.payment_failed
```
> **Validación:** Confirmar visualmente el banner de "Pago Pendiente" o el error 402 en consola de red. No documentar si el webhook falla o el bypass de desarrollo está roto.

### 3. Actualizar Documentación de Infraestructura & Orquestación
Revisar la carpeta `infrastructure/` y verificar que el `README.md` maestro esté alineado con los puertos y servicios actuales.
Ejemplos críticos a verificar:
*   `infrastructure/README.md`: ¿La matriz de decisión sigue siendo válida?
*   `infrastructure/docker/docker-compose.dev.yml`: ¿Los healthchecks están operativos?
*   `infrastructure/docker/migrate_all.ps1`: ¿Se agregaron los nuevos microservicios al barrido de migraciones?

### 3.5. Validación del Ecosistema Local (Ping Maestro)
Asegurar que el orquestador esté levantado y enrutando correctamente antes de documentar:
// turbo
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_ecosystem.ps1
```
> **Validación:** Confirmar que todos los servicios reporten `[ OK ]` o estatus HTTP esperados, garantizando la salud del API Gateway.

### 4. Actualizar Bitácoras de Ingeniería (REPO_LOG y SERVICE_LOG)
Escribir un resumen breve en el `REPO_LOG.md` raíz con los detalles de la fase actual (Objetivos, Decisiones Arquitectónicas y Workarounds).

**IMPORTANTE:** Replicar un resumen técnico adaptado en el respectivo `SERVICE_LOG.md` de cada microservicio afectado y en el `README_DEV.md` de la infraestructura si hubo cambios en puertos o variables.

### 4.5. Consolidados Diarios y Planes de Implementación
Para no contaminar la raíz documental, dividir y clasificar la jornada obligatoriamente respetando esta nomenclatura estricta:
- **Tareas del Día**: Crear o actualizar `docs/historial/tasks/consolidated_tasksYYYYMMDD.md` (Ej. `consolidated_tasks20260420.md`) capturando backlog superado y pendientes.
- **Planes de Implementación**: Crear archivo `docs/historial/implementation/master_implementation_historyYYYYMMDD.md` (Ej. `master_implementation_history20260420.md`) registrando la arquitectura planeada/ejecutada del día.

### 5. Confirmación Segura (Git Versioning)
Finalmente, empaquetar de forma segura toda la arquitectura confirmando el commit.
// turbo
```bash
git add .
git commit -m "docs(architecture): Phase completion and sync-docs audit"
```

## Criterios de Éxito
- `generate_code_graph.py` compila al 100% (Limpieza).
- Los Markdowns en `/docs` reflejan comandos copiables y verídicos sobre la última iteración.
- `REPO_LOG.md` cuenta la historia del estado actual de forma secuencial.
