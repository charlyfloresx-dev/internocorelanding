# InternoCore: Protocolo de Sincronización de Documentación (Sync-Docs)

Este flujo de trabajo garantiza que la "fuente de verdad" documental esté siempre alineada con el código desplegado, evitando la deuda técnica y manteniendo el control arquitectónico (FinOps, Seguridad y Estructura).

## Disparadores (Triggers)
Ejecutar este workflow cuando:
1. Se despliega un nuevo microservicio en AWS (ECS o App Runner).
2. Se resuelve un bug crítico que involucra cambios en configuración (`env`, dependencias, DB).
3. Se finaliza una Fase Arquitectónica importante.

## Tareas

### 1. Auditoría del Gráfico de Código (Code Graph)
Ejecutar el script de auditoría automatizada para validar _Invariants_ (FinOps, CORS, multi-tenant):
// turbo
```bash
python backend/scripts/generate_code_graph.py
```
> **Validación:** Si el script falla con Exit Code 1 o reporta Errores Críticos (Ej. Inicios de Load Balancer que rompan el presupuesto), detener el workflow de documentación y avisar al usuario. No documentar arquitectura inválida.

### 2. Generar Status Report (Punto de Control)
Si la auditoría es limpia, invocar el comando para generar un reporte del estado diario. Esto resumirá la fase completada.
```text
/status-report
```

### 3. Actualizar Documentación FinOps & Infraestructura
Revisar la carpeta `docs/infraestructura/` y verificar si es necesario actualizar alguna de las guías base basándose en los comandos y flujos estabilizados recientemente.
Ejemplos críticos a verificar:
*   `APP_RUNNER_DEPLOY_GUIDE.md`: Chequear si existen nuevos parámetros o límites encontrados (ej. Cuotas).
*   `AWS_Deployment_Strategy.md`: Actualizar topología si se migró un frontend o se cambió el plan.

### 4. Actualizar REPO_LOG.md (Bitácora Maestra y Microservicios)
Escribir un resumen breve en el `REPO_LOG.md` raíz con los siguientes detalles de la fase actual:
1. Número de la Fase y Objetivo (Ej. *Estabilización App Runner*).
2. Tareas técnicas completadas con éxito.
3. Decisiones Arquitectónicas o Workarounds aplicados.

**IMPORTANTE:** Replicar un resumen técnico adaptado en el respectivo `REPO_LOG.md` de cada microservicio afectado (Ej. `backend/auth_service/REPO_LOG.md`) para mantener su contexto individualizado.

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
